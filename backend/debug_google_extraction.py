#!/usr/bin/env python3
"""Debug Google PDF extraction"""

import os
import fitz
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# Test file that should have -6,284.42
filepath = os.path.join('..', 'Invoice for testing', '5297692790.pdf')

print("="*80)
print("DEBUGGING: 5297692790.pdf (should be -6,284.42)")
print("="*80)

with fitz.open(filepath) as doc:
    print(f"Total pages: {len(doc)}")
    
    # Check page 1 for total
    if len(doc) >= 1:
        page1 = doc[0]
        text1 = page1.get_text()
        print("\nPage 1 - Looking for total:")
        lines = text1.split('\n')
        for i, line in enumerate(lines):
            if 'ยอดเงินครบกำหนด' in line or 'Amount due' in line or '-6,284.42' in line or '6,284.42' in line:
                print(f"  Line {i}: {line}")
                # Show next 5 lines
                for j in range(1, 6):
                    if i + j < len(lines):
                        print(f"  Line {i+j}: {lines[i+j]}")
    
    # Check page 2 for line items
    if len(doc) >= 2:
        page2 = doc[1]
        text2 = page2.get_text()
        
        print("\nPage 2 - Looking for line items:")
        
        # Find all amounts
        amounts = []
        lines = text2.split('\n')
        for i, line in enumerate(lines):
            # Look for amount patterns
            if re.search(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', line):
                amounts.append((i, line.strip()))
        
        print(f"Found {len(amounts)} potential amounts:")
        for line_num, amount_line in amounts[:10]:
            print(f"  Line {line_num}: {amount_line}")
        
        # Try blocks extraction
        print("\nUsing blocks extraction:")
        blocks = page2.get_text("blocks")
        print(f"Total blocks: {len(blocks)}")
        
        # Look for amounts in blocks
        amount_blocks = []
        for idx, block in enumerate(blocks):
            if len(block) >= 5:
                block_text = block[4].strip()
                if re.search(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', block_text):
                    amount_blocks.append((idx, block_text))
        
        print(f"\nFound {len(amount_blocks)} amount blocks:")
        for idx, text in amount_blocks[:10]:
            print(f"  Block {idx}: {text}")
        
        # Calculate total from found amounts
        total = 0
        for _, text in amount_blocks:
            match = re.search(r'(-?\d{1,3}(?:,\d{3})*\.\d{2})', text)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    if abs(amount) < 100000:  # Reasonable amount
                        total += amount
                except:
                    pass
        
        print(f"\nCalculated total from page 2: {total:,.2f}")

# Also check 5297785878.pdf
print("\n" + "="*80)
print("DEBUGGING: 5297785878.pdf (should have 1 line with -1.66)")
print("="*80)

filepath2 = os.path.join('..', 'Invoice for testing', '5297785878.pdf')
with fitz.open(filepath2) as doc:
    print(f"Total pages: {len(doc)}")
    
    # Get all text
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    
    # Look for -1.66
    if '-1.66' in full_text:
        print("Found -1.66 in text")
        # Find context
        idx = full_text.find('-1.66')
        print(f"Context:\n{full_text[idx-100:idx+100]}")
    elif '1.66' in full_text:
        print("Found 1.66 (without minus) in text")
        idx = full_text.find('1.66')
        print(f"Context:\n{full_text[idx-100:idx+100]}")