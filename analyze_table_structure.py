#!/usr/bin/env python3

import os
import re
from PyPDF2 import PdfReader

def analyze_table_structure(invoice_number):
    """Analyze the table structure of a specific TikTok invoice"""
    
    invoice_dir = "Invoice for testing"
    filename = f"{invoice_number}-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    print(f"Analyzing table structure for: {invoice_number}")
    print("=" * 80)
    
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        lines = text_content.split('\n')
        
        # Find consumption details section
        in_consumption = False
        consumption_lines = []
        
        for i, line in enumerate(lines):
            if 'Consumption Details:' in line:
                in_consumption = True
                continue
            
            if in_consumption:
                if any(stop in line.lower() for stop in ['total in thb', 'please note']):
                    break
                consumption_lines.append((i, line))
        
        print("\nCONSUMPTION TABLE LINES (first 50):")
        print("-" * 80)
        
        for i, (line_num, line) in enumerate(consumption_lines[:50]):
            print(f"{line_num:4d}: {line}")
        
        print("\n\nANALYZING TABLE STRUCTURE:")
        print("-" * 80)
        
        # Look for patterns that indicate row boundaries
        print("\n1. Lines starting with ST (Statement IDs):")
        st_lines = [(n, l) for n, l in consumption_lines if re.match(r'^ST\d+', l.strip())]
        for n, l in st_lines[:10]:
            print(f"  Line {n}: {l.strip()}")
        
        print(f"\nTotal ST lines found: {len(st_lines)}")
        
        print("\n2. Lines with amount patterns (Total, Voucher, Cash):")
        amount_lines = []
        for n, l in consumption_lines:
            # Pattern: number 0.00 number (indicating Total, Voucher, Cash)
            if re.search(r'\d+\.\d{2}\s*0\.00\s*\d+\.\d{2}', l):
                amount_lines.append((n, l))
        
        for n, l in amount_lines[:10]:
            print(f"  Line {n}: {l.strip()}")
        
        print(f"\nTotal amount lines found: {len(amount_lines)}")
        
        print("\n3. Checking if amounts are split across lines:")
        # Look for lines that contain only amounts
        solo_amount_lines = []
        for n, l in consumption_lines:
            line_clean = l.strip()
            # Line contains only numbers, commas, periods, and spaces
            if re.match(r'^[\d,.\s]+$', line_clean) and '.' in line_clean:
                solo_amount_lines.append((n, l))
        
        print(f"Found {len(solo_amount_lines)} lines with only amounts")
        for n, l in solo_amount_lines[:10]:
            print(f"  Line {n}: {l.strip()}")
        
        # Check the expected total
        print("\n4. Verifying expected total vs actual rows:")
        expected_total = 173380.83
        
        # Try to reconstruct rows properly
        print("\nReconstructing table rows manually...")
        
        # Manually parse specific pattern seen in this invoice
        # The amounts seem to be on separate lines
        reconstructed_rows = []
        i = 0
        while i < len(consumption_lines):
            _, line = consumption_lines[i]
            line = line.strip()
            
            # If line starts with ST, it's a new row
            if re.match(r'^ST\d+', line):
                row_data = {'st': line}
                
                # Collect next few lines for this row
                j = 1
                while i + j < len(consumption_lines) and j < 15:  # Max 15 lines per row
                    _, next_line = consumption_lines[i + j]
                    next_line = next_line.strip()
                    
                    # Check if this is the amounts line
                    if re.match(r'^[\d,.\s]+$', next_line) and next_line.count('.') >= 2:
                        # This looks like the amounts line
                        amounts = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d{2})', next_line)
                        if len(amounts) >= 3:
                            row_data['amounts'] = amounts
                            reconstructed_rows.append(row_data)
                            i = i + j + 1
                            break
                    j += 1
                else:
                    i += 1
            else:
                i += 1
        
        print(f"\nReconstructed {len(reconstructed_rows)} rows")
        
        total_from_rows = 0
        for idx, row in enumerate(reconstructed_rows):
            if 'amounts' in row and len(row['amounts']) >= 3:
                cash_amount = float(row['amounts'][2].replace(',', ''))
                total_from_rows += cash_amount
                print(f"  Row {idx+1}: {row['st'][:20]}... Cash: {cash_amount:,.2f}")
        
        print(f"\nTotal from reconstructed rows: {total_from_rows:,.2f}")
        print(f"Expected total: {expected_total:,.2f}")
        print(f"Difference: {expected_total - total_from_rows:,.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Analyze the invoice with the biggest discrepancy
    analyze_table_structure("THTT202502215912")