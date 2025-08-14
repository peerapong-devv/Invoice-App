#!/usr/bin/env python3
"""Analyze specific Google invoice file in detail"""

import os
import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Analyze 5297692778.pdf which should have total 18,550.72
filepath = os.path.join('..', 'Invoice for testing', '5297692778.pdf')

print("="*80)
print("ANALYZING 5297692778.pdf (should be 18,550.72 THB)")
print("="*80)

with fitz.open(filepath) as doc:
    print(f"Total pages: {len(doc)}")
    
    # Check page 1 for total
    if len(doc) >= 1:
        page1 = doc[0]
        text1 = page1.get_text()
        
        # Look for total
        print("\nPage 1 - Searching for total:")
        lines = text1.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'18,550\.72|18550\.72', line):
                print(f"  Found total at line {i}: {line}")
                # Show context
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    print(f"    {j}: {lines[j]}")
    
    # Check page 2 for line items
    if len(doc) >= 2:
        page2 = doc[1]
        blocks = page2.get_text("blocks")
        
        print("\n\nPage 2 - Line items:")
        print(f"Total blocks: {len(blocks)}")
        
        # Find amounts
        amounts = []
        for idx, block in enumerate(blocks):
            if len(block) >= 5:
                text = block[4].strip()
                # Look for amounts
                if re.search(r'\d+,?\d*\.\d{2}', text):
                    amounts.append((idx, text))
        
        print(f"\nFound {len(amounts)} potential amounts:")
        for idx, text in amounts:
            print(f"  Block {idx}: {text}")
        
        # Calculate total
        total = 0
        for _, text in amounts:
            # Extract all amounts from the text
            amount_matches = re.findall(r'(-?\d{1,3}(?:,\d{3})*\.\d{2})', text)
            for amount_str in amount_matches:
                try:
                    amount = float(amount_str.replace(',', ''))
                    if 0 < amount < 100000:  # Reasonable range
                        total += amount
                        print(f"    Adding: {amount:,.2f}")
                except:
                    pass
        
        print(f"\nCalculated total: {total:,.2f}")
        
        # Look for the main amount 18,550.72
        print("\nSearching for 18,550.72 in page 2:")
        page2_text = page2.get_text()
        if '18,550.72' in page2_text:
            print("  Found 18,550.72 in page 2")
            idx = page2_text.find('18,550.72')
            print(f"  Context: {page2_text[idx-50:idx+50]}")

# Also check 5297735036.pdf
print("\n\n" + "="*80)
print("ANALYZING 5297735036.pdf (should be 79,988.30 THB)")
print("="*80)

filepath2 = os.path.join('..', 'Invoice for testing', '5297735036.pdf')
with fitz.open(filepath2) as doc:
    if len(doc) >= 2:
        page2 = doc[1]
        text = page2.get_text()
        
        # Look for the main amount
        if '79,988.30' in text:
            print("Found 79,988.30 in text")
            idx = text.find('79,988.30')
            print(f"Context: {text[idx-100:idx+100]}")
        
        # Get all amounts
        amounts = re.findall(r'(-?\d{1,3}(?:,\d{3})*\.\d{2})', text)
        print(f"\nAll amounts found: {len(amounts)}")
        for i, amt in enumerate(amounts[:20]):
            print(f"  {i+1}. {amt}")