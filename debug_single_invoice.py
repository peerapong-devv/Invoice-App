#!/usr/bin/env python3

import os
import sys
from PyPDF2 import PdfReader

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from final_tiktok_parser import parse_tiktok_invoice_final

def debug_single_invoice(invoice_number):
    """Debug a single invoice parsing"""
    
    invoice_dir = "Invoice for testing"
    filename = f"{invoice_number}-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    print(f"Debugging invoice: {invoice_number}")
    print("=" * 80)
    
    try:
        # Read PDF
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        print("Text content preview (first 1000 chars):")
        print(text_content[:1000])
        print("\n" + "=" * 80)
        
        # Check for key patterns
        print("Pattern checks:")
        print(f"  Has 'Consumption Details:': {'Consumption Details:' in text_content}")
        has_st = bool(re.search(r'ST\d{10,}', text_content))
        print(f"  Has ST pattern: {has_st}")
        print(f"  Has pk| pattern: {'pk|' in text_content}")
        
        # Find consumption details section
        consumption_start = text_content.find('Consumption Details:')
        if consumption_start != -1:
            print(f"\nConsumption Details found at position: {consumption_start}")
            consumption_text = text_content[consumption_start:consumption_start+500]
            print("Consumption section preview:")
            print(consumption_text)
        else:
            print("\nNo 'Consumption Details:' found!")
            # Try alternative patterns
            alt_patterns = ['Consumption', 'Details', 'Campaign', 'Statement']
            for pattern in alt_patterns:
                if pattern in text_content:
                    pos = text_content.find(pattern)
                    print(f"\nFound '{pattern}' at position {pos}:")
                    print(text_content[pos:pos+200])
        
        print("\n" + "=" * 80)
        print("Attempting to parse...")
        
        # Parse with current parser
        records = parse_tiktok_invoice_final(text_content, filename)
        
        print(f"Parsed {len(records)} records")
        for i, record in enumerate(records):
            print(f"\nRecord {i+1}:")
            for key, value in record.items():
                if value:
                    print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import re
    # Test with the first invoice
    debug_single_invoice("THTT202502215482")