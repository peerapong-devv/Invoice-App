#!/usr/bin/env python3

import os
import re
from PyPDF2 import PdfReader
from backend.working_tiktok_parser_lookup import parse_tiktok_invoice_lookup
from backend.fixed_tiktok_line_parser import parse_tiktok_invoice_detailed

def verify_fixed_parser():
    """Verify the fixed parser matches the lookup table results"""
    
    invoice_dir = "Invoice for testing"
    
    # Get all TikTok invoice files
    tiktok_files = [f for f in os.listdir(invoice_dir) 
                    if f.startswith('THTT') and f.endswith('.pdf')]
    tiktok_files.sort()
    
    print(f"Verifying fixed parser on {len(tiktok_files)} TikTok invoice files...")
    print("=" * 100)
    
    # Results tracking
    lookup_results = {}
    fixed_results = {}
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
            fixed_records = parse_tiktok_invoice_detailed(text_content, filename)
            
            # Calculate totals
            lookup_total = sum(r.get('amount', 0) for r in lookup_records)
            fixed_total = sum(r.get('amount', 0) for r in fixed_records)
            
            # Store results
            lookup_results[invoice_number] = lookup_total
            fixed_results[invoice_number] = fixed_total
            
            # Check for differences
            if abs(lookup_total - fixed_total) > 0.01:  # Allow tiny rounding differences
                differences.append({
                    'invoice': invoice_number,
                    'lookup': lookup_total,
                    'fixed': fixed_total,
                    'difference': lookup_total - fixed_total,
                    'fixed_lines': len(fixed_records)
                })
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Print summary
    lookup_grand_total = sum(lookup_results.values())
    fixed_grand_total = sum(fixed_results.values())
    
    print("\nSUMMARY:")
    print(f"Lookup Parser Total (CORRECT): {lookup_grand_total:,.2f} THB")
    print(f"Fixed Parser Total:            {fixed_grand_total:,.2f} THB")
    print(f"Difference:                    {lookup_grand_total - fixed_grand_total:,.2f} THB")
    print(f"Number of invoices with differences: {len(differences)}")
    
    if abs(lookup_grand_total - fixed_grand_total) < 0.01:
        print("\n✅ SUCCESS! The fixed parser now matches the lookup table exactly!")
    else:
        print("\n❌ Still have differences. Details below:")
        
        # Print differences in detail
        if differences:
            print("\nDETAILED DIFFERENCES:")
            print("-" * 100)
            print(f"{'Invoice Number':<20} {'Lookup (Correct)':<20} {'Fixed Parser':<20} {'Difference':<20}")
            print("-" * 100)
            
            for diff in sorted(differences, key=lambda x: abs(x['difference']), reverse=True):
                print(f"{diff['invoice']:<20} {diff['lookup']:>19,.2f} {diff['fixed']:>19,.2f} "
                      f"{diff['difference']:>19,.2f}")
    
    return fixed_grand_total == lookup_grand_total

if __name__ == "__main__":
    verify_fixed_parser()