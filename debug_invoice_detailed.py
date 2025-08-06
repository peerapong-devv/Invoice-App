#!/usr/bin/env python3

import os
import sys
import re
from PyPDF2 import PdfReader

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from final_tiktok_parser import parse_tiktok_invoice_final

def debug_invoice_parsing(invoice_number):
    """Debug invoice parsing in detail"""
    
    invoice_dir = "Invoice for testing"
    filename = f"{invoice_number}-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    try:
        # Read PDF
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        print(f"Debugging invoice: {invoice_number}")
        print("=" * 80)
        
        # Check invoice type detection
        has_st_pattern = bool(re.search(r'ST\d{10,}', text_content))
        has_pk_pattern = bool(re.search(r'pk\|', text_content))
        is_ap = has_st_pattern and has_pk_pattern
        
        print(f"Invoice Type Detection:")
        print(f"  Has ST pattern: {has_st_pattern}")
        print(f"  Has pk| pattern: {has_pk_pattern}")
        print(f"  Detected as: {'AP' if is_ap else 'Non-AP'}")
        
        # Find consumption details
        consumption_start = text_content.find('Consumption Details:')
        if consumption_start == -1:
            print("\nERROR: No 'Consumption Details:' section found!")
            return
        
        consumption_text = text_content[consumption_start:]
        lines = consumption_text.split('\n')
        
        print(f"\nConsumption section has {len(lines)} lines")
        print("\nFirst 20 lines of consumption section:")
        for i, line in enumerate(lines[:20]):
            print(f"{i:3}: '{line.strip()}'")
        
        # For Non-AP, look for campaign lines with 'pk' but not 'pk|'
        if not is_ap:
            print("\n" + "=" * 80)
            print("Searching for Non-AP campaign lines...")
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # Check if line contains 'pk' and is not a header/amount
                if 'pk' in line_stripped.lower() and not ('pk|' in line_stripped or '[ST]' in line_stripped):
                    if not re.match(r'^[\d,]+\.\d{2}$', line_stripped) and line_stripped not in ['Statement', 'Campaign Name', 'Target Country']:
                        print(f"\nPotential campaign at line {i}: '{line_stripped}'")
                        
                        # Look for amounts in next lines
                        for j in range(i+1, min(i+10, len(lines))):
                            next_line = lines[j].strip()
                            if re.match(r'^[\d,]+\.\d{2}$', next_line):
                                print(f"  Found amount at line {j}: {next_line}")
        
        # Try parsing
        print("\n" + "=" * 80)
        print("Parsing result:")
        records = parse_tiktok_invoice_final(text_content, filename)
        print(f"Found {len(records)} records")
        
        total = sum(r.get('total', 0) or 0 for r in records)
        print(f"Total amount parsed: {total:,.2f} THB")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with different invoices
    test_invoices = ["THTT202502215482", "THTT202502215575", "THTT202502216319"]
    
    for inv in test_invoices:
        debug_invoice_parsing(inv)
        print("\n" + "="*100 + "\n")