#!/usr/bin/env python3

import os
import sys
from PyPDF2 import PdfReader

# Add backend to path to import parsers
sys.path.append('./backend')

# Import all the different parsers
try:
    from working_google_parser_lookup import parse_google_invoice_lookup
    from enhanced_google_parser import parse_google_invoice_enhanced  
    from perfect_google_parser import parse_google_invoice_perfect
    from ultra_perfect_google_parser import parse_google_invoice_ultra
    from corrected_google_parser import parse_google_invoice_exact
    print("Successfully imported all basic parsers")
except ImportError as e:
    print(f"Error importing basic parsers: {e}")
    sys.exit(1)

# Try to import additional parsers
additional_parsers = []
try:
    from learned_google_parser import parse_google_invoice_learned
    additional_parsers.append((parse_google_invoice_learned, "Learned Parser"))
except ImportError:
    pass

try:  
    from comprehensive_google_parser import parse_google_invoice_comprehensive
    additional_parsers.append((parse_google_invoice_comprehensive, "Comprehensive Parser"))
except ImportError:
    pass

try:
    from final_google_parser import parse_google_invoice_complete
    additional_parsers.append((parse_google_invoice_complete, "Final Parser (Complete)"))
except ImportError:
    pass

def test_parser_with_details(parser_func, parser_name, test_files):
    """Test a parser and report both totals and detail extraction"""
    
    print(f"\n{'='*60}")
    print(f"TESTING: {parser_name}")
    print(f"{'='*60}")
    
    total_amount = 0
    detailed_files = 0
    successful_files = 0
    
    for filename in test_files:
        filepath = os.path.join("Invoice for testing", filename)
        
        if not os.path.exists(filepath):
            continue
            
        try:
            # Read PDF content
            with open(filepath, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                text_content = ''.join([page.extract_text() for page in reader.pages])
            
            # Parse with this parser
            records = parser_func(text_content, filename)
            
            if records:
                file_total = sum(r.get('total', 0) or r.get('amount', 0) for r in records if r.get('total') or r.get('amount'))
                total_amount += file_total
                successful_files += 1
                
                # Check for detailed extraction (more than just total)
                has_detailed_data = False
                for record in records:
                    if (record.get('agency') or 
                        record.get('project_id') or 
                        record.get('campaign_id') or
                        record.get('objective')):
                        has_detailed_data = True
                        break
                
                if has_detailed_data or len(records) > 1:
                    detailed_files += 1
                
                # Show first few records for AP files to check detail extraction
                if 'pk|' in text_content and len(records) <= 5:
                    print(f"\n{filename} (AP): {len(records)} records, total: {file_total:,.2f}")
                    for i, record in enumerate(records[:3]):
                        agency = record.get('agency', 'N/A')
                        proj_id = record.get('project_id', 'N/A') 
                        campaign = record.get('campaign_id', 'N/A')
                        obj = record.get('objective', 'N/A')
                        amount = record.get('total', 0)
                        print(f"  {i+1}. Agency:{agency} ProjID:{proj_id} Camp:{campaign} Obj:{obj} Amt:{amount}")
                        
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    print(f"\nSUMMARY for {parser_name}:")
    print(f"  Files processed: {successful_files}")
    print(f"  Files with detailed data: {detailed_files}")
    print(f"  Total amount: {total_amount:,.2f} THB")
    print(f"  Expected: 2,362,684.79 THB")
    print(f"  Difference: {abs(total_amount - 2362684.79):,.2f} THB")
    print(f"  Accuracy: {'PERFECT' if abs(total_amount - 2362684.79) < 0.01 else 'INCORRECT'}")
    
    return {
        'name': parser_name,
        'total': total_amount,
        'files_processed': successful_files,
        'detailed_files': detailed_files,
        'accurate': abs(total_amount - 2362684.79) < 0.01
    }

def main():
    # Get all Google invoice files
    invoice_dir = "Invoice for testing"
    if not os.path.exists(invoice_dir):
        print(f"Invoice directory not found: {invoice_dir}")
        return
    
    all_files = os.listdir(invoice_dir)
    google_files = [f for f in all_files if f.startswith('529') or f.startswith('530')]
    google_files.sort()
    
    print(f"Found {len(google_files)} Google invoice files")
    
    # Test different parsers
    parsers_to_test = [
        (parse_google_invoice_lookup, "Lookup Parser (working_google_parser_lookup)"),
        (parse_google_invoice_enhanced, "Enhanced Parser"),
        (parse_google_invoice_perfect, "Perfect Parser"), 
        (parse_google_invoice_ultra, "Ultra Perfect Parser"),
        (parse_google_invoice_exact, "Exact Parser (corrected)"),
    ]
    
    # Add additional parsers if they were imported successfully
    parsers_to_test.extend(additional_parsers)
    
    results = []
    
    for parser_func, parser_name in parsers_to_test:
        try:
            result = test_parser_with_details(parser_func, parser_name, google_files)
            results.append(result)
        except Exception as e:
            print(f"\nError testing {parser_name}: {e}")
    
    # Summary of all results
    print(f"\n{'='*80}")
    print("FINAL COMPARISON - PARSERS WITH CORRECT TOTALS AND DETAILED EXTRACTION")
    print(f"{'='*80}")
    
    accurate_parsers = [r for r in results if r['accurate']]
    
    if accurate_parsers:
        print("Parsers with CORRECT total (2,362,684.79 THB):")
        for result in accurate_parsers:
            print(f"  >> {result['name']}")
            print(f"    Files processed: {result['files_processed']}")
            print(f"    Files with detailed data: {result['detailed_files']}")
            print(f"    Total: {result['total']:,.2f} THB")
            print()
    else:
        print("X No parsers found with the correct total!")
    
    print("\nAll parser results:")
    for result in results:
        status = "CORRECT" if result['accurate'] else "WRONG"
        print(f"  {status} {result['name']}: {result['total']:,.2f} THB ({result['detailed_files']}/{result['files_processed']} detailed)")

if __name__ == "__main__":
    main()