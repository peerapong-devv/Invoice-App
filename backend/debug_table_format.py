#!/usr/bin/env python3
"""Debug table format Google invoices"""

import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Test file that should have 11 items
filepath = '../Invoice for testing/5298156820.pdf'

with fitz.open(filepath) as doc:
    # Get text from all pages
    full_text = ''
    for page_num, page in enumerate(doc):
        text = page.get_text()
        full_text += text
        
        # Check page 2 specifically (where table usually is)
        if page_num == 1:
            print(f"Page 2 content analysis:")
            lines = text.split('\n')
            
            # Find table area
            for i, line in enumerate(lines):
                if 'คำอธิบาย' in line:
                    print(f"\nTable header found at line {i}")
                    # Show next 50 lines
                    for j in range(i, min(i + 50, len(lines))):
                        # Check for patterns
                        if 'DMCRM' in lines[j] or 'DMHEALTH' in lines[j]:
                            print(f"Line {j}: Campaign - {lines[j][:60]}")
                        elif re.match(r'^\d{7,}$', lines[j].strip()):
                            print(f"Line {j}: ID - {lines[j].strip()}")
                        elif re.match(r'^\d{1,3}(?:,\d{3})*\.\d{2}$', lines[j].strip()):
                            print(f"Line {j}: Amount - {lines[j].strip()}")
                        elif '\u200b' in lines[j]:
                            # Clean fragmented text
                            clean = lines[j].replace('\u200b', '').strip()
                            if clean:
                                print(f"Line {j}: Fragmented - {clean[:60]}")

# Count expected line items
print("\n\nAnalyzing full text for campaign patterns:")
campaigns = re.findall(r'(DMCRM[^|]+\|[^|]+|DMHEALTH[^|]+\|[^|]+)', full_text)
print(f"Found {len(campaigns)} campaign patterns")

# Count amounts
amounts = re.findall(r'(?:^|\s)(\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', full_text, re.MULTILINE)
valid_amounts = [float(a.replace(',', '')) for a in amounts if 100 < float(a.replace(',', '')) < 500000]
print(f"Found {len(valid_amounts)} valid amounts in item range")