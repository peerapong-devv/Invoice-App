#!/usr/bin/env python3
"""Check why some files are missing duplicate amounts"""

import os
import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def check_file(filename):
    """Check line structure in detail"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Checking: {filename}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        if len(doc) < 2:
            return
        
        page2 = doc[1]
        text = page2.get_text()
        lines = text.split('\n')
        
        # Find all lines with the specific amounts we're missing
        target_amounts = {
            '5297692778.pdf': 18482.50,
            '5297692787.pdf': 18875.00,
            '5298156820.pdf': 801728.42,
            '5300624442.pdf': 214728.05
        }
        
        if filename in target_amounts:
            target = target_amounts[filename]
            
            print(f"\nLooking for amount: {target:,.2f}")
            
            count = 0
            for i, line in enumerate(lines):
                if f"{target:,.2f}" in line or f"{target:.2f}" in line:
                    count += 1
                    print(f"\nFound at line {i}: {line.strip()}")
                    
                    # Show context
                    print("Context:")
                    for j in range(max(0, i-5), min(i+2, len(lines))):
                        prefix = ">>>" if j == i else "   "
                        print(f"{prefix} {j:3d}: {lines[j].strip()[:80]}")
            
            print(f"\nTotal occurrences: {count}")

# Check the 4 problematic files
files = [
    '5297692778.pdf',
    '5297692787.pdf', 
    '5298156820.pdf',
    '5300624442.pdf'
]

for f in files:
    check_file(f)