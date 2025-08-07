#!/usr/bin/env python3
"""Debug specific Google files that have wrong totals"""

import os
import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def debug_file(filename, expected_total):
    """Debug a specific file"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Debugging: {filename}")
    print(f"Expected total: {expected_total:,.2f}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        # Check all pages
        all_amounts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Find all amounts
            amount_pattern = r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})'
            amounts = re.findall(amount_pattern, text)
            
            for amt in amounts:
                try:
                    amount = float(amt.replace(',', ''))
                    if 0.01 <= abs(amount) <= 10000000:
                        all_amounts.append((page_num + 1, amount))
                except:
                    pass
        
        print(f"\nTotal amounts found across all pages: {len(all_amounts)}")
        
        # Group by page
        page1_amounts = [amt for page, amt in all_amounts if page == 1]
        page2_amounts = [amt for page, amt in all_amounts if page == 2]
        
        print(f"Page 1 amounts: {len(page1_amounts)}")
        print(f"Page 2 amounts: {len(page2_amounts)}")
        
        # Try different combinations to match expected total
        print("\nSearching for combination that equals expected total...")
        
        # Check page 2 amounts only
        page2_sum = sum(page2_amounts)
        print(f"\nSum of all page 2 amounts: {page2_sum:,.2f}")
        
        # For files with big discrepancy, look for missing large amounts
        if abs(page2_sum - expected_total) > 1000:
            print("\nLarge discrepancy detected. Looking for missing amounts...")
            
            # Check if expected total appears anywhere
            for page_num, amount in all_amounts:
                if abs(amount - expected_total) < 0.01:
                    print(f"  Found expected total on page {page_num}: {amount:,.2f}")
                elif abs(amount - expected_total/2) < 100:
                    print(f"  Found half of expected on page {page_num}: {amount:,.2f}")
        
        # Show unique amounts on page 2
        unique_page2 = sorted(set(page2_amounts), key=lambda x: abs(x), reverse=True)
        print(f"\nUnique amounts on page 2 ({len(unique_page2)} unique):")
        for amt in unique_page2[:10]:
            count = page2_amounts.count(amt)
            print(f"  {amt:>12,.2f} (appears {count}x)")

# Debug problematic files
problems = [
    ('5297692778.pdf', 36965.00),  # Got 18,482.50, missing half
    ('5297692787.pdf', 56626.86),  # Got 18,875.00, missing 37,751.86
    ('5298156820.pdf', 1603456.84),  # Got 801,728.42, missing half
    ('5300624442.pdf', 429456.10),  # Got 214,728.05, missing half
]

for filename, expected in problems:
    debug_file(filename, expected)