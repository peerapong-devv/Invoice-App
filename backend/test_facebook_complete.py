#!/usr/bin/env python3
"""Test complete Facebook parser on specific problem files"""

import os
import sys
import fitz
from facebook_parser_complete import parse_facebook_invoice

sys.stdout.reconfigure(encoding='utf-8')

# Test specific problem files
problem_files = {
    '246543739.pdf': 1985559.44,
    '246546622.pdf': 974565.49  # From the report
}

invoice_dir = os.path.join('..', 'Invoice for testing')

for filename, expected_total in problem_files.items():
    filepath = os.path.join(invoice_dir, filename)
    
    print(f"\n{'='*80}")
    print(f"Testing: {filename}")
    print(f"Expected total: {expected_total:,.2f}")
    print('='*80)
    
    # Read text
    with fitz.open(filepath) as doc:
        text_content = ""
        for page in doc:
            text_content += page.get_text()
    
    # Parse
    items = parse_facebook_invoice(text_content, filename)
    
    # Calculate total
    total = sum(item['amount'] for item in items)
    
    print(f"\nExtracted {len(items)} items")
    print(f"Total: {total:,.2f}")
    print(f"Difference: {total - expected_total:,.2f}")
    
    # Show negative items
    negative_items = [item for item in items if item['amount'] < 0]
    if negative_items:
        print(f"\nNegative amounts found: {len(negative_items)}")
        for item in negative_items:
            print(f"  Line {item['line_number']}: {item['amount']:,.2f}")
            print(f"    Description: {item['description'][:80]}...")
    else:
        print("\nWARNING: No negative amounts found!")
    
    # Show first few items
    print("\nFirst 5 items:")
    for item in items[:5]:
        print(f"  Line {item['line_number']}: {item['amount']:>12,.2f} - {item['description'][:50]}...")
    
    # Show last few items
    if len(items) > 5:
        print(f"\nLast 5 items:")
        for item in items[-5:]:
            print(f"  Line {item['line_number']}: {item['amount']:>12,.2f} - {item['description'][:50]}...")

# Also test overall totals
print("\n" + "="*80)
print("TESTING ALL FACEBOOK FILES")
print("="*80)

facebook_files = sorted([f for f in os.listdir(invoice_dir) if f.startswith('24') and f.endswith('.pdf')])
print(f"Processing {len(facebook_files)} files...")

all_items = []
files_with_negatives = 0

for filename in facebook_files:
    filepath = os.path.join(invoice_dir, filename)
    
    # Read text
    with fitz.open(filepath) as doc:
        text_content = ""
        for page in doc:
            text_content += page.get_text()
    
    # Parse
    items = parse_facebook_invoice(text_content, filename)
    
    # Check for negatives
    has_negatives = any(item['amount'] < 0 for item in items)
    if has_negatives:
        files_with_negatives += 1
    
    all_items.extend(items)

# Calculate overall total
overall_total = sum(item['amount'] for item in all_items)
negative_count = sum(1 for item in all_items if item['amount'] < 0)
negative_total = sum(item['amount'] for item in all_items if item['amount'] < 0)

print(f"\nTotal items: {len(all_items)}")
print(f"Files with negative amounts: {files_with_negatives}")
print(f"Total negative items: {negative_count}")
print(f"Total negative amount: {negative_total:,.2f}")
print(f"Overall total: {overall_total:,.2f}")
print(f"Expected total: 12,831,605.92")
print(f"Difference: {overall_total - 12831605.92:,.2f}")