#!/usr/bin/env python3

import os
import re
from PyPDF2 import PdfReader
from backend.working_tiktok_parser_lookup import parse_tiktok_invoice_lookup
from backend.enhanced_tiktok_line_parser_v2_final import parse_tiktok_invoice_detailed

def compare_tiktok_parsers():
    """Compare TikTok lookup parser (correct) vs detailed parser results"""
    
    invoice_dir = "Invoice for testing"
    
    # Get all TikTok invoice files
    tiktok_files = [f for f in os.listdir(invoice_dir) 
                    if f.startswith('THTT') and f.endswith('.pdf')]
    tiktok_files.sort()
    
    print(f"Comparing {len(tiktok_files)} TikTok invoice files...")
    print("=" * 100)
    
    # Results tracking
    lookup_results = {}
    detailed_results = {}
    differences = []
    
    # Process each file
    for filename in tiktok_files:
        file_path = os.path.join(invoice_dir, filename)
        invoice_number = filename.replace('-Prakit Holdings Public Company Limited-Invoice.pdf', '')
        
        try:
            # Read PDF
            with open(file_path, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                text_content = ''.join([page.extract_text() for page in reader.pages])
            
            # Parse with both parsers
            lookup_records = parse_tiktok_invoice_lookup(text_content, filename)
            detailed_records = parse_tiktok_invoice_detailed(text_content, filename)
            
            # Calculate totals
            lookup_total = sum(r.get('amount', 0) for r in lookup_records)
            detailed_total = sum(r.get('amount', 0) for r in detailed_records)
            
            # Store results
            lookup_results[invoice_number] = lookup_total
            detailed_results[invoice_number] = detailed_total
            
            # Check for differences
            if abs(lookup_total - detailed_total) > 0.01:  # Allow tiny rounding differences
                differences.append({
                    'invoice': invoice_number,
                    'lookup': lookup_total,
                    'detailed': detailed_total,
                    'difference': lookup_total - detailed_total,
                    'detailed_lines': len(detailed_records)
                })
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Print summary
    lookup_grand_total = sum(lookup_results.values())
    detailed_grand_total = sum(detailed_results.values())
    
    print("\nSUMMARY:")
    print(f"Lookup Parser Total:   {lookup_grand_total:,.2f} THB (CORRECT)")
    print(f"Detailed Parser Total: {detailed_grand_total:,.2f} THB")
    print(f"Difference:            {lookup_grand_total - detailed_grand_total:,.2f} THB")
    print(f"Number of invoices with differences: {len(differences)}")
    
    # Print differences in detail
    if differences:
        print("\nDETAILED DIFFERENCES:")
        print("-" * 100)
        print(f"{'Invoice Number':<20} {'Lookup (Correct)':<20} {'Detailed Parser':<20} {'Difference':<20} {'Lines'}")
        print("-" * 100)
        
        differences_sorted = sorted(differences, key=lambda x: abs(x['difference']), reverse=True)
        
        for diff in differences_sorted:
            print(f"{diff['invoice']:<20} {diff['lookup']:>19,.2f} {diff['detailed']:>19,.2f} "
                  f"{diff['difference']:>19,.2f} {diff['detailed_lines']:>5}")
    
    # Analyze specific problematic invoices
    print("\nANALYZING PROBLEMATIC INVOICES:")
    print("-" * 100)
    
    # Focus on top 5 biggest differences
    for i, diff in enumerate(differences_sorted[:5]):
        print(f"\n{i+1}. Invoice {diff['invoice']}:")
        print(f"   Expected: {diff['lookup']:,.2f} THB")
        print(f"   Got:      {diff['detailed']:,.2f} THB")
        print(f"   Missing:  {diff['difference']:,.2f} THB")
        
        # Re-parse to get details
        file_path = os.path.join(invoice_dir, f"{diff['invoice']}-Prakit Holdings Public Company Limited-Invoice.pdf")
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                text_content = ''.join([page.extract_text() for page in reader.pages])
            
            detailed_records = parse_tiktok_invoice_detailed(text_content, f"{diff['invoice']}-Prakit Holdings Public Company Limited-Invoice.pdf")
            
            if detailed_records:
                print(f"   Detailed parser extracted {len(detailed_records)} line(s)")
                for j, record in enumerate(detailed_records):
                    print(f"     Line {j+1}: {record.get('amount', 0):,.2f} THB - {record.get('description', 'No description')}")
            else:
                print("   Detailed parser found NO records!")
                
        except Exception as e:
            print(f"   Error re-parsing: {e}")
    
    return lookup_results, detailed_results, differences

if __name__ == "__main__":
    compare_tiktok_parsers()