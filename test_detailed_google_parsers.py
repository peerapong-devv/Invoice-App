#!/usr/bin/env python3

import os
import sys
from PyPDF2 import PdfReader

# Add backend to path to import parsers
sys.path.append('./backend')

# Import the parsers that get correct totals
from working_google_parser_lookup import parse_google_invoice_lookup
from corrected_google_parser import parse_google_invoice_exact

def test_detailed_extraction(parser_func, parser_name, test_files):
    """Test detailed data extraction for AP invoices"""
    
    print(f"\n{'='*80}")
    print(f"DETAILED EXTRACTION TEST: {parser_name}")
    print(f"{'='*80}")
    
    total_amount = 0
    ap_files_processed = 0
    ap_files_with_details = 0
    
    # Test specific AP files to check detailed extraction
    ap_test_files = [
        "5298248238.pdf",  # Known AP with multiple campaigns
        "5297692787.pdf",  # Known AP with multiple campaigns  
        "5297692799.pdf",  # Known AP with multiple campaigns
        "5298130144.pdf",  # Known AP
        "5298240989.pdf"   # Known AP
    ]
    
    for filename in ap_test_files:
        filepath = os.path.join("Invoice for testing", filename)
        
        if not os.path.exists(filepath):
            print(f"  File not found: {filename}")
            continue
            
        try:
            # Read PDF content
            with open(filepath, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                text_content = ''.join([page.extract_text() for page in reader.pages])
            
            # Check if it's actually an AP invoice
            is_ap = 'pk|' in text_content
            if not is_ap:
                print(f"  {filename}: Not an AP invoice (no pk| pattern found)")
                continue
            
            # Parse with this parser
            records = parser_func(text_content, filename)
            
            if records:
                file_total = sum(r.get('total', 0) or r.get('amount', 0) for r in records if r.get('total') or r.get('amount'))
                total_amount += file_total
                ap_files_processed += 1
                
                print(f"\n  {filename} (AP Invoice): {len(records)} records, total: {file_total:,.2f} THB")
                
                # Check for detailed extraction
                has_detailed_data = False
                detailed_records = 0
                
                for i, record in enumerate(records):
                    agency = record.get('agency', 'N/A')
                    proj_id = record.get('project_id', 'N/A') 
                    proj_name = record.get('project_name', 'N/A')
                    campaign = record.get('campaign_id', 'N/A')
                    objective = record.get('objective', 'N/A')
                    period = record.get('period', 'N/A')
                    amount = record.get('total', 0) or record.get('amount', 0)
                    desc = record.get('description', 'N/A')[:100]
                    
                    if (agency and agency != 'N/A' and agency != 'Unknown') or \
                       (proj_id and proj_id != 'N/A' and proj_id != 'Unknown') or \
                       (campaign and campaign != 'N/A' and campaign != 'Unknown') or \
                       (objective and objective != 'N/A' and objective != 'Unknown'):
                        has_detailed_data = True
                        detailed_records += 1
                    
                    if i < 3:  # Show first 3 records
                        print(f"    {i+1}. Agency:{agency} ProjID:{proj_id} Camp:{campaign}")
                        print(f"       Objective:{objective} Amount:{amount} Desc:{desc}")
                
                if has_detailed_data:
                    ap_files_with_details += 1
                    print(f"    >> HAS DETAILED DATA: {detailed_records}/{len(records)} records with details")
                else:
                    print(f"    >> NO DETAILED DATA: Only basic amounts extracted")
                        
        except Exception as e:
            print(f"  Error processing {filename}: {e}")
            continue
    
    print(f"\nSUMMARY for {parser_name}:")
    print(f"  AP files processed: {ap_files_processed}")
    print(f"  AP files with detailed data: {ap_files_with_details}")
    print(f"  Total amount: {total_amount:,.2f} THB")
    
    return {
        'name': parser_name,
        'total': total_amount,
        'ap_processed': ap_files_processed,
        'ap_detailed': ap_files_with_details,
        'has_line_details': ap_files_with_details > 0
    }

def main():
    # Test the parsers that get correct totals
    parsers_to_test = [
        (parse_google_invoice_lookup, "Lookup Parser (working_google_parser_lookup)"),
        (parse_google_invoice_exact, "Exact Parser (corrected_google_parser)"),
    ]
    
    results = []
    
    for parser_func, parser_name in parsers_to_test:
        try:
            result = test_detailed_extraction(parser_func, parser_name, [])
            results.append(result)
        except Exception as e:
            print(f"\nError testing {parser_name}: {e}")
    
    # Summary
    print(f"\n{'='*80}")
    print("FINAL RESULTS: CORRECT TOTAL + DETAILED EXTRACTION")
    print(f"{'='*80}")
    
    perfect_parsers = [r for r in results if r['has_line_details']]
    
    if perfect_parsers:
        print("Parsers with CORRECT total AND detailed line-by-line extraction:")
        for result in perfect_parsers:
            print(f"  >> {result['name']}")
            print(f"     AP files with details: {result['ap_detailed']}/{result['ap_processed']}")
            print()
    else:
        print("No parsers found with both correct totals AND detailed extraction!")
        print("\nParsers with correct totals but no detailed extraction:")
        for result in results:
            status = "DETAILED" if result['has_line_details'] else "BASIC ONLY"
            print(f"  {result['name']}: {status}")

if __name__ == "__main__":
    main()