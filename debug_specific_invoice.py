#!/usr/bin/env python3

import os
import re
from PyPDF2 import PdfReader

def debug_invoice(invoice_number):
    """Debug specific TikTok invoice to find missing amounts"""
    
    invoice_dir = "Invoice for testing"
    filename = f"{invoice_number}-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    print(f"Debugging invoice: {invoice_number}")
    print("=" * 80)
    
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        # Look for consumption details section
        lines = text_content.split('\n')
        
        print("\n1. LOOKING FOR CONSUMPTION DETAILS SECTION:")
        print("-" * 80)
        
        in_consumption = False
        consumption_lines = []
        
        for i, line in enumerate(lines):
            if 'Consumption Details:' in line:
                in_consumption = True
                print(f"Found at line {i}: {line}")
                continue
            
            if in_consumption:
                if any(stop in line.lower() for stop in ['total in thb', 'please note']):
                    print(f"End at line {i}: {line}")
                    break
                if line.strip():
                    consumption_lines.append(line.strip())
        
        print(f"\nFound {len(consumption_lines)} consumption lines")
        
        print("\n2. LOOKING FOR AMOUNTS IN CONSUMPTION SECTION:")
        print("-" * 80)
        
        # Find all monetary amounts
        all_amounts = []
        for line in consumption_lines:
            # Find amounts in format 1,234.56
            amounts = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d{2})', line)
            for amt in amounts:
                try:
                    value = float(amt.replace(',', ''))
                    all_amounts.append((value, line))
                except:
                    pass
        
        print(f"Found {len(all_amounts)} amounts in consumption section:")
        for amt, line in sorted(all_amounts, key=lambda x: x[0], reverse=True)[:20]:
            print(f"  {amt:>12,.2f} THB in: {line[:80]}...")
        
        # Calculate total from amounts
        unique_amounts = set(amt for amt, _ in all_amounts)
        print(f"\nTotal of all unique amounts: {sum(unique_amounts):,.2f} THB")
        
        print("\n3. LOOKING FOR INVOICE TOTAL:")
        print("-" * 80)
        
        for i, line in enumerate(lines):
            if 'total amount due' in line.lower():
                print(f"Line {i}: {line}")
                # Look at next few lines too
                for j in range(1, 5):
                    if i+j < len(lines):
                        print(f"Line {i+j}: {lines[i+j]}")
        
        print("\n4. PATTERN ANALYSIS FOR MISSING AMOUNTS:")
        print("-" * 80)
        
        # Look for patterns that might indicate missing rows
        st_patterns = re.findall(r'ST\d+', text_content)
        print(f"Found {len(st_patterns)} ST patterns (potential rows)")
        
        # Look for campaign patterns
        campaign_patterns = re.findall(r'([A-Z][A-Za-z\s]+(?:Campaign|VDO|Content|KOL)[^\n]*)', text_content)
        print(f"Found {len(campaign_patterns)} campaign patterns")
        
        # Count actual data rows by looking for the pattern of amounts at end of row
        row_end_pattern = r'\d{1,3}(?:,\d{3})*\.\d{2}\s+0\.00\s+\d{1,3}(?:,\d{3})*\.\d{2}'
        row_ends = re.findall(row_end_pattern, text_content)
        print(f"Found {len(row_ends)} complete row endings (Total, Voucher, Cash pattern)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Debug the most problematic invoice
if __name__ == "__main__":
    # Invoice with biggest difference
    debug_invoice("THTT202502215912")