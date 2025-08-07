#!/usr/bin/env python3
"""Test complete Google parser on problem files"""

import os
import sys
import fitz
from google_parser_complete import parse_google_invoice

sys.stdout.reconfigure(encoding='utf-8')

# Test specific problem files
problem_files = {
    '5297692778.pdf': {
        'expected_total': 36965.00,
        'expected_items': 3,
        'issue': 'Was extracting 4 items (included subtotal)'
    },
    '5297692787.pdf': {
        'expected_total': 56626.86,
        'expected_items': 8,
        'issue': 'Missing AP field extraction'
    },
    '5297732883.pdf': {
        'expected_total': 7756.04,
        'has_fee': True,
        'issue': 'Missing fee from last page'
    },
    '5297786049.pdf': {
        'expected_total': 4905.61,
        'has_fee': True,
        'issue': 'Missing fee from last page'
    }
}

invoice_dir = os.path.join('..', 'Invoice for testing')

print("="*80)
print("TESTING GOOGLE PARSER ON PROBLEM FILES")
print("="*80)

for filename, info in problem_files.items():
    filepath = os.path.join(invoice_dir, filename)
    
    print(f"\n{'='*60}")
    print(f"Testing: {filename}")
    print(f"Issue: {info['issue']}")
    print(f"Expected total: {info['expected_total']:,.2f}")
    if 'expected_items' in info:
        print(f"Expected items: {info['expected_items']}")
    print('='*60)
    
    # Read text
    with fitz.open(filepath) as doc:
        text_content = ""
        for page in doc:
            text_content += page.get_text()
    
    # Parse
    items = parse_google_invoice(text_content, filepath)
    
    # Calculate total
    total = sum(item['amount'] for item in items)
    
    print(f"\nResults:")
    print(f"  Extracted items: {len(items)}")
    print(f"  Total: {total:,.2f}")
    print(f"  Difference: {total - info['expected_total']:,.2f}")
    
    # Check specific issues
    if filename == '5297692778.pdf':
        # Check if 18,482.50 is included
        has_subtotal = any(abs(item['amount'] - 18482.50) < 0.01 for item in items)
        print(f"  Contains 18,482.50 subtotal: {'YES (ERROR)' if has_subtotal else 'NO (CORRECT)'}")
    
    if filename == '5297692787.pdf':
        # Check AP fields
        ap_items = [item for item in items if item.get('agency') == 'pk']
        print(f"  Items with AP fields: {len(ap_items)}")
        if ap_items:
            print(f"  Sample AP item: {ap_items[0]['description'][:50]}...")
            print(f"    Project ID: {ap_items[0].get('project_id')}")
            print(f"    Campaign ID: {ap_items[0].get('campaign_id')}")
    
    if info.get('has_fee'):
        # Check for fee items
        fee_items = [item for item in items if 'fee' in item['description'].lower() or 'ค่าธรรมเนียม' in item['description']]
        print(f"  Fee items found: {len(fee_items)}")
        for fee in fee_items:
            print(f"    {fee['description']}: {fee['amount']:.2f}")
    
    # Show all items
    print(f"\nAll items:")
    for item in items:
        print(f"  {item['line_number']:2d}. {item['amount']:>10,.2f} - {item['description'][:50]}...")

# Test all Google files
print("\n" + "="*80)
print("TESTING ALL GOOGLE FILES")
print("="*80)

google_files = sorted([f for f in os.listdir(invoice_dir) if f.startswith('5') and f.endswith('.pdf')])
print(f"Processing {len(google_files)} files...")

all_items = []
correct_count = 0

# Expected totals
EXPECTED_TOTALS = {
    '5297692778': 36965.00,
    '5297692787': 56626.86,
    '5297732883': 7756.04,
    '5297786049': 4905.61,
    # Add more as needed
}

for filename in google_files[:10]:  # Test first 10 files
    filepath = os.path.join(invoice_dir, filename)
    
    # Read text
    with fitz.open(filepath) as doc:
        text_content = ""
        for page in doc:
            text_content += page.get_text()
    
    # Parse
    items = parse_google_invoice(text_content, filepath)
    
    # Calculate total
    total = sum(item['amount'] for item in items)
    
    # Check if correct
    invoice_num = filename.replace('.pdf', '')
    expected = EXPECTED_TOTALS.get(invoice_num, 0)
    
    if expected > 0:
        diff = abs(total - expected)
        is_correct = diff < 0.01
        if is_correct:
            correct_count += 1
        
        status = "✓" if is_correct else "✗"
        print(f"{status} {filename}: {len(items)} items, Total: {total:,.2f} (Expected: {expected:,.2f})")
    else:
        print(f"  {filename}: {len(items)} items, Total: {total:,.2f}")
    
    all_items.extend(items)

print(f"\nTotal items extracted: {len(all_items)}")
print(f"Files with correct totals: {correct_count}/{len(EXPECTED_TOTALS)}")