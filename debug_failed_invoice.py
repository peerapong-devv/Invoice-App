#!/usr/bin/env python3

import re
import os
from PyPDF2 import PdfReader

def debug_invoice(invoice_number):
    """Debug why an invoice is failing to parse"""
    
    invoice_dir = "Invoice for testing"
    filename = f"{invoice_number}-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        print(f"Debugging {invoice_number}")
        print("="*80)
        
        # Find all ST patterns
        st_pattern = re.compile(r'(ST\d{10,})')
        st_matches = list(st_pattern.finditer(text_content))
        print(f"Found {len(st_matches)} ST patterns")
        
        # Find consumption details
        consumption_start = text_content.find('Consumption Details:')
        if consumption_start == -1:
            print("ERROR: No 'Consumption Details:' found!")
            # Try to find it with variations
            for variant in ['Consumption', 'Details']:
                pos = text_content.find(variant)
                if pos != -1:
                    print(f"Found '{variant}' at position {pos}")
                    print(text_content[pos:pos+100])
            return
        
        consumption_text = text_content[consumption_start:]
        
        # Find ST patterns in consumption section
        st_in_consumption = list(st_pattern.finditer(consumption_text))
        print(f"Found {len(st_in_consumption)} ST patterns in consumption section")
        
        # Check for amounts
        amount_pattern = re.compile(r'([\d,]+\.\d{2})')
        amounts = amount_pattern.findall(consumption_text)
        print(f"Found {len(amounts)} amounts: {amounts[:10]}...")  # Show first 10
        
        # Show the first ST section in detail
        if st_in_consumption:
            first_st = st_in_consumption[0]
            st_id = first_st.group(1)
            start_pos = first_st.end()
            
            # Find end (next ST or 500 chars)
            if len(st_in_consumption) > 1:
                end_pos = st_in_consumption[1].start()
            else:
                end_pos = min(start_pos + 500, len(consumption_text))
            
            section = consumption_text[start_pos:end_pos]
            
            print(f"\nFirst ST section ({st_id}):")
            print("-"*80)
            print(section)
            print("-"*80)
            
            # Show as lines
            print("\nAs lines:")
            lines = section.split('\n')
            for i, line in enumerate(lines[:20]):
                print(f"{i:3}: '{line.strip()}'")
            
            # Check for pk| pattern
            has_pk = 'pk|' in section
            print(f"\nHas pk| pattern: {has_pk}")
            
            # Find amounts in this section
            section_amounts = amount_pattern.findall(section)
            print(f"Amounts in section: {section_amounts}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Debug some failed invoices
    failed_invoices = ["THTT202502215482", "THTT202502216319", "THTT202502215645"]
    
    for inv in failed_invoices[:2]:
        debug_invoice(inv)
        print("\n" + "="*100 + "\n")