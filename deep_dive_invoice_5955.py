#!/usr/bin/env python3

import os
import re
from PyPDF2 import PdfReader

def deep_dive_invoice():
    """Deep dive into invoice THTT202502215955 to find missing amount"""
    
    invoice_dir = "Invoice for testing"
    filename = "THTT202502215955-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        print("DEEP DIVE: THTT202502215955")
        print("Expected total: 178,218.52")
        print("=" * 80)
        
        # Look for the total amount in the invoice
        total_match = re.search(r'Total Amount Due\s*([\d,]+\.\d{2})', text_content)
        if total_match:
            print(f"Invoice shows Total Amount Due: {total_match.group(1)}")
        
        # Find all concatenated amount patterns
        amount_pattern = r'\d{1,3}(?:,\d{3})*\.\d{2}0\.00\d{1,3}(?:,\d{3})*\.\d{2}'
        concat_amounts = re.findall(amount_pattern, text_content)
        
        print(f"\nFound {len(concat_amounts)} concatenated amount patterns")
        
        # Also look for the special pattern where amounts might be split differently
        # Check for lines containing "138,240"
        if "138,240" in text_content:
            print("\nFound reference to 138,240 amount")
            # Extract context around this amount
            context = re.findall(r'.{0,50}138,240.{0,50}', text_content)
            for c in context:
                print(f"  Context: {c}")
        
        # Look for all lines in consumption section
        lines = text_content.split('\n')
        in_consumption = False
        consumption_lines = []
        
        for line in lines:
            if 'Consumption Details:' in line:
                in_consumption = True
                continue
            if in_consumption:
                if 'total in thb' in line.lower():
                    break
                consumption_lines.append(line)
        
        print(f"\nConsumption section has {len(consumption_lines)} lines")
        
        # Look for all amount patterns in consumption section
        print("\nAll amounts in consumption section:")
        all_amounts = []
        for line in consumption_lines:
            amounts = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d{2})', line)
            for amt in amounts:
                try:
                    value = float(amt.replace(',', ''))
                    all_amounts.append(value)
                    if value > 10000:  # Show larger amounts
                        print(f"  {amt} in line: {line[:60]}...")
                except:
                    pass
        
        print(f"\nSum of all unique amounts found: {sum(set(all_amounts)):,.2f}")
        
        # Manually check for the missing 138,240.00
        print("\n\nSearching for 138,240 pattern specifically...")
        pattern_138k = re.findall(r'138[,\s]*240(?:\.\d{2})?', text_content)
        print(f"Found {len(pattern_138k)} instances of 138,240 pattern")
        
        # Check if amounts might be formatted differently
        print("\n\nChecking for amounts with different formatting...")
        # Look for pattern like: number number number (three amounts in sequence)
        triple_pattern = r'(\d{1,3}(?:,\d{3})*\.\d{2})\s*(\d{1,3}(?:,\d{3})*\.\d{2})\s*(\d{1,3}(?:,\d{3})*\.\d{2})'
        triple_amounts = re.findall(triple_pattern, text_content)
        
        print(f"Found {len(triple_amounts)} triple amount patterns:")
        total_from_triples = 0
        for t1, t2, t3 in triple_amounts:
            try:
                v1 = float(t1.replace(',', ''))
                v2 = float(t2.replace(',', ''))
                v3 = float(t3.replace(',', ''))
                # t2 should be 0.00 (voucher), t3 is cash
                if v2 == 0.0:
                    total_from_triples += v3
                    print(f"  Total: {t1}, Voucher: {t2}, Cash: {t3}")
            except:
                pass
        
        print(f"\nTotal from triple patterns: {total_from_triples:,.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deep_dive_invoice()