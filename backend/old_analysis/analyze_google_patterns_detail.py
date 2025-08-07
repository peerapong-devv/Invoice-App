#!/usr/bin/env python3
"""Analyze specific patterns in Google invoices to understand structure better"""

import os
import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def analyze_invoice_detail(filepath, filename):
    """Analyze invoice in more detail"""
    
    print(f"\n{'='*80}")
    print(f"Analyzing: {filename}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        if len(doc) < 2:
            print("Less than 2 pages!")
            return
        
        # Get page 2 where line items are
        page2 = doc[1]
        page2_text = page2.get_text()
        
        # Clean text
        page2_text = page2_text.replace('\u200b', '')
        lines = page2_text.split('\n')
        
        # Find table section
        table_start = -1
        table_end = -1
        
        for i, line in enumerate(lines):
            if any(marker in line for marker in ['คำอธิบาย', 'Description', 'รายละเอียด']):
                table_start = i
                print(f"Table starts at line {i}: {line.strip()}")
                break
        
        # Find where amounts start appearing
        amount_lines = []
        for i, line in enumerate(lines):
            if re.search(r'\d{1,3}(?:,\d{3})*\.\d{2}', line):
                amount_lines.append((i, line.strip()))
        
        print(f"\nFound {len(amount_lines)} lines with amounts")
        
        # Show structure around first few amounts
        print("\nStructure around amounts:")
        for idx, (line_no, amount_line) in enumerate(amount_lines[:5]):
            print(f"\n--- Amount #{idx+1} at line {line_no} ---")
            
            # Show 5 lines before and the amount line
            for i in range(max(0, line_no-5), line_no+1):
                prefix = ">>>" if i == line_no else "   "
                print(f"{prefix} {i:3d}: {lines[i].strip()[:100]}")
            
            # Check if this looks like a line item
            amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})', amount_line)
            if amount_match:
                amount = float(amount_match.group(1).replace(',', ''))
                
                # Look for description pattern
                desc_found = False
                for j in range(max(0, line_no-10), line_no):
                    check_line = lines[j].strip()
                    if '|' in check_line:
                        print(f"    Found pipe pattern at line {j}: {check_line[:80]}")
                        desc_found = True
                        break
                    elif 'การคลิก' in check_line:
                        print(f"    Found 'การคลิก' at line {j}")
                        desc_found = True
                    elif 'กิจกรรมที่ไม่ถูกต้อง' in check_line:
                        print(f"    Found credit pattern at line {j}")
                        desc_found = True
                        break
                
                if not desc_found:
                    print(f"    WARNING: No clear description pattern found for amount {amount}")

# Test on a few different types
test_files = [
    '5297692778.pdf',  # Has multiple items
    '5298156820.pdf',  # Has DMCRM/DMHEALTH patterns
    '5302951835.pdf',  # Has 20 items!
    '5297969160.pdf',  # Has 0 items extracted
]

for filename in test_files:
    filepath = os.path.join('..', 'Invoice for testing', filename)
    if os.path.exists(filepath):
        analyze_invoice_detail(filepath, filename)