#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug Google invoice structure"""

import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Debug invoice 5298156820.pdf in detail
filepath = '../Invoice for testing/5298156820.pdf'

with fitz.open(filepath) as doc:
    print(f"Analyzing {filepath}")
    print(f"Pages: {len(doc)}")
    
    # Check each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split('\n')
        
        print(f"\n{'='*80}")
        print(f"PAGE {page_num + 1}")
        print('='*80)
        
        # Look for table structure
        for i, line in enumerate(lines):
            if 'คำอธิบาย' in line or 'Description' in line:
                print(f"\nFound header at line {i}: {line}")
                # Show next 30 lines
                for j in range(i, min(i+30, len(lines))):
                    print(f"{j:3}: {repr(lines[j][:100])}")
                break
        
        # Also look for amounts with context
        amount_pattern = re.compile(r'^\s*(\d{1,3}(?:,\d{3})*\.\d{2})\s*$')
        
        print(f"\n\nAmounts found on page {page_num + 1}:")
        for i, line in enumerate(lines):
            if amount_pattern.match(line.strip()):
                amount = line.strip()
                print(f"\nAmount: {amount}")
                # Show context
                for j in range(max(0, i-3), min(len(lines), i+2)):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{j:3}: {lines[j][:80]}")