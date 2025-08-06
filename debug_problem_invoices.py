#!/usr/bin/env python3

import os
import sys
import re
from PyPDF2 import PdfReader

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fixed_tiktok_concatenation_parser import parse_tiktok_invoice_fixed

def debug_specific_invoice(invoice_number, expected_amount):
    """Debug a specific invoice with incorrect amount"""
    
    invoice_dir = "Invoice for testing"
    filename = f"{invoice_number}-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        print(f"Debugging {invoice_number} (Expected: {expected_amount:,.2f})")
        print("="*80)
        
        # Parse with fixed parser
        records = parse_tiktok_invoice_fixed(text_content, filename)
        parsed_total = sum(r['total'] for r in records if r['total'])
        
        print(f"Parsed {len(records)} records, Total: {parsed_total:,.2f}")
        print(f"Missing: {expected_amount - parsed_total:,.2f} THB")
        
        print("\nParsed Records:")
        for i, record in enumerate(records, 1):
            print(f"{i:2}: {record['total']:>10,.2f} - {record['description'][:50]}...")
        
        # Find consumption section and look for all amounts
        consumption_start = text_content.find('Consumption Details:')
        consumption_text = text_content[consumption_start:]
        
        # Find all amounts in the text
        amounts = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d{2})', consumption_text)
        unique_amounts = list(set([float(a.replace(',', '')) for a in amounts]))
        unique_amounts.sort(reverse=True)
        
        print(f"\nAll amounts found in text ({len(unique_amounts)} unique):")
        for amt in unique_amounts[:20]:  # Show top 20
            print(f"  {amt:>10,.2f}")
        
        # Look for subtotal or total sections
        if 'Subtotal' in text_content:
            subtotal_pos = text_content.find('Subtotal')
            subtotal_section = text_content[subtotal_pos:subtotal_pos+200]
            print(f"\nSubtotal section:")
            print(subtotal_section)
        
        # Look for the final total
        total_matches = re.findall(r'Total.*?(\d{1,3}(?:,\d{3})*\.\d{2})', text_content, re.IGNORECASE)
        if total_matches:
            print(f"\nTotal amounts found:")
            for total in total_matches:
                print(f"  {float(total.replace(',', '')):,.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Debug the invoices with the largest missing amounts
    problem_invoices = [
        ("THTT202502215912", 173380.83),  # Missing 41,713.93
        ("THTT202502215645", 357261.56),  # Missing 25,271.13
        ("THTT202502216210", 272794.74),  # Missing 25,472.02
    ]
    
    for invoice, expected in problem_invoices:
        debug_specific_invoice(invoice, expected)
        print("\n" + "="*100 + "\n")