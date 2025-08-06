#!/usr/bin/env python3
"""Test extracting patterns from Google invoices"""

import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def analyze_invoice(filepath):
    """Analyze invoice to extract patterns"""
    
    with fitz.open(filepath) as doc:
        full_text = ''
        for page in doc:
            full_text += page.get_text()
    
    # Clean text
    full_text = full_text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    lines = full_text.split('\n')
    
    # Find table area
    table_start = -1
    table_end = -1
    
    for i, line in enumerate(lines):
        if 'คำอธิบาย' in line:
            table_start = i
            print(f"Table starts at line {i}")
        elif table_start > -1 and ('ยอดรวม' in line or 'จำนวนเงินรวม' in line):
            table_end = i
            print(f"Table ends at line {i}")
            break
    
    if table_start == -1:
        print("No table found")
        return
    
    # Extract patterns from table area
    print("\nExtracting patterns from table area:")
    print("-" * 80)
    
    i = table_start + 3  # Skip header
    items_found = []
    
    while i < (table_end if table_end > -1 else len(lines)):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Look for pattern indicators
        if any(p in line for p in ['pk|', 'pk｜', 'DMCRM', 'DMHEALTH', 'กิจกรรม', 'ค่าธรรมเนียม']):
            # Found potential item
            desc = line
            
            # Look for amount in next 10 lines
            for j in range(i + 1, min(i + 10, len(lines))):
                amount_line = lines[j].strip()
                
                # Check if it's an amount
                if re.match(r'^-?\d{1,3}(?:,\d{3})*\.?\d{2}$', amount_line):
                    amount = float(amount_line.replace(',', ''))
                    
                    # Check if valid amount range
                    if 0.01 <= abs(amount) <= 1000000:
                        items_found.append({
                            'description': desc,
                            'amount': amount,
                            'line_desc': i,
                            'line_amt': j
                        })
                        print(f"Item {len(items_found)}:")
                        print(f"  Desc (line {i}): {desc[:80]}...")
                        print(f"  Amount (line {j}): {amount:,.2f}")
                        i = j  # Skip to after amount
                        break
        
        i += 1
    
    print(f"\nTotal items found: {len(items_found)}")
    total = sum(item['amount'] for item in items_found)
    print(f"Total amount: {total:,.2f}")
    
    return items_found

# Test on files with known patterns
test_files = [
    ('5297692778.pdf', 3, 18482.50),
    ('5297692799.pdf', 7, 8578.86),
    ('5298156820.pdf', 11, 801728.42)
]

for filename, expected_items, expected_total in test_files:
    filepath = f'../Invoice for testing/{filename}'
    print(f"\n{'='*80}")
    print(f"Testing {filename}")
    print(f"Expected: {expected_items} items, total {expected_total:,.2f}")
    print('='*80)
    
    items = analyze_invoice(filepath)
    
    if items:
        actual_total = sum(item['amount'] for item in items)
        print(f"\nResult: {len(items)} items, total {actual_total:,.2f}")
        
        if len(items) == expected_items:
            print("✓ Correct number of items")
        else:
            print(f"✗ Wrong number of items (expected {expected_items})")
            
        if abs(actual_total - expected_total) < 0.01:
            print("✓ Correct total")
        else:
            print(f"✗ Wrong total (diff: {actual_total - expected_total:,.2f})")