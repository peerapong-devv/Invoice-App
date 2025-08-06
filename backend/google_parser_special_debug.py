#!/usr/bin/env python3
"""Debug Google invoice fragmented text"""

import fitz
import re

# Test the 3 problematic files
files = ['5297692778.pdf', '5297692787.pdf', '5297692790.pdf']

for filename in files:
    filepath = f'../Invoice for testing/{filename}'
    print(f"\n{'='*80}")
    print(f"Analyzing {filename}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        # Get text from all pages
        full_text = ''
        for page in doc:
            full_text += page.get_text()
        
        lines = full_text.split('\n')
        
        # Find table area
        in_table = False
        for i, line in enumerate(lines):
            if 'คำอธิบาย' in line:
                in_table = True
                print(f"\nTable starts at line {i}")
                continue
                
            if in_table and ('ยอดรวม' in line or 'จำนวนเงินรวม' in line):
                in_table = False
                print(f"Table ends at line {i}")
                break
                
            if in_table and line.strip():
                # Check if line contains fragmented text
                if '\u200b' in line or '\u200c' in line or '\u200d' in line:
                    print(f"Line {i} (FRAGMENTED): {repr(line[:50])}")
                elif re.match(r'^\d{1,3}(?:,\d{3})*\.\d{2}$', line.strip()):
                    print(f"Line {i} (AMOUNT): {line.strip()}")
                elif 'pk|' in line or 'pk｜' in line:
                    print(f"Line {i} (PK PATTERN): {line[:50]}")