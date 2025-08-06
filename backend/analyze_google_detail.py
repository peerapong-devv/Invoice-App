#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze Google invoice in detail to understand line item structure"""

import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Analyze invoice 5298156820 which has 11 potential line items
filepath = '../Invoice for testing/5298156820.pdf'

with fitz.open(filepath) as doc:
    print(f"Analyzing {filepath}")
    print(f"Pages: {len(doc)}")
    
    # Look at page 2 which usually has line items
    if len(doc) > 1:
        page2_text = doc[1].get_text()
        lines = page2_text.split('\n')
        
        print("\nLooking for line items pattern on page 2:")
        print("="*80)
        
        # Find amounts and their context
        amount_pattern = re.compile(r'^\s*(-?\d{1,3}(?:,\d{3})*\.?\d{2})\s*$')
        
        for i, line in enumerate(lines):
            match = amount_pattern.match(line.strip())
            if match:
                amount = float(match.group(1).replace(',', ''))
                if 100 < abs(amount) < 500000:  # Reasonable range for line items
                    print(f"\nAmount found: {amount:,.2f}")
                    
                    # Show context
                    start = max(0, i-5)
                    end = min(len(lines), i+3)
                    
                    for j in range(start, end):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{j:3}: {lines[j][:100]}")
        
        # Check if there's a pattern in the structure
        print("\n\nChecking for table structure:")
        print("="*80)
        
        # Look for header patterns
        for i, line in enumerate(lines[:50]):
            if any(word in line for word in ['คำอธิบาย', 'Description', 'ปริมาณ', 'Quantity', 'จำนวนเงิน', 'Amount']):
                print(f"Header at line {i}: {line}")
                
                # Show next 10 lines
                for j in range(i+1, min(i+11, len(lines))):
                    print(f"  {j}: {lines[j][:100]}")