#!/usr/bin/env python3
"""Analyze Facebook parser totals to find discrepancy"""

import os
import sys
import fitz
from facebook_parser_enhanced_ap import parse_facebook_invoice

sys.stdout.reconfigure(encoding='utf-8')

# Expected totals - from user's comment
EXPECTED_TOTAL = 12831605.92
ACTUAL_TOTAL = 12834251.15
DIFFERENCE = ACTUAL_TOTAL - EXPECTED_TOTAL  # 2,645.23

print("="*80)
print("FACEBOOK TOTALS ANALYSIS")
print("="*80)
print(f"Expected total: {EXPECTED_TOTAL:,.2f}")
print(f"Actual total: {ACTUAL_TOTAL:,.2f}")
print(f"Difference: {DIFFERENCE:,.2f}")
print("="*80)

# Test all Facebook files
invoice_dir = os.path.join('..', 'Invoice for testing')
facebook_files = sorted([f for f in os.listdir(invoice_dir) if f.startswith('24') and f.endswith('.pdf')])

print(f"\nProcessing {len(facebook_files)} Facebook invoice files...")
print("="*80)

all_items = []
file_totals = []

for idx, filename in enumerate(facebook_files):
    filepath = os.path.join(invoice_dir, filename)
    
    # Read text
    with fitz.open(filepath) as doc:
        text_content = ""
        for page in doc:
            text_content += page.get_text()
    
    # Parse
    items = parse_facebook_invoice(text_content, filename)
    
    # Calculate file total
    file_total = sum(item['amount'] for item in items)
    
    file_totals.append({
        'filename': filename,
        'items_count': len(items),
        'total': file_total,
        'items': items
    })
    
    all_items.extend(items)
    
    # Show progress
    print(f"[{idx+1:2d}/{len(facebook_files)}] {filename}: {len(items)} items, Total: {file_total:,.2f}")

# Calculate overall total
overall_total = sum(item['amount'] for item in all_items)

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Total files: {len(facebook_files)}")
print(f"Total items: {len(all_items)}")
print(f"Overall total: {overall_total:,.2f}")
print(f"Expected total: {EXPECTED_TOTAL:,.2f}")
print(f"Difference: {overall_total - EXPECTED_TOTAL:,.2f}")

# Check for potential issues
print("\n" + "="*80)
print("CHECKING FOR ISSUES")
print("="*80)

# Look for duplicate amounts
from collections import Counter
amounts = [item['amount'] for item in all_items]
amount_counts = Counter(amounts)

# Find amounts that appear suspiciously often
suspicious_amounts = [(amt, count) for amt, count in amount_counts.items() if count > 5 and abs(amt) > 100]
if suspicious_amounts:
    print("\nAmounts appearing frequently (potential duplicates):")
    for amt, count in sorted(suspicious_amounts, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {amt:>12,.2f} appears {count} times")

# Check for specific amount that matches the difference
print(f"\nLooking for amounts close to the difference ({DIFFERENCE:,.2f})...")
for item in all_items:
    if abs(abs(item['amount']) - DIFFERENCE) < 1:
        print(f"  Found: {item['amount']:,.2f} in {item['filename']}")
        print(f"    Description: {item.get('description', 'N/A')}")

# Check for negative amounts that might be counted incorrectly
negative_items = [item for item in all_items if item['amount'] < 0]
negative_total = sum(item['amount'] for item in negative_items)
print(f"\nNegative amounts:")
print(f"  Count: {len(negative_items)}")
print(f"  Total: {negative_total:,.2f}")

# Check if any files have parsing errors
print("\nChecking for potential parsing errors...")
for file_data in file_totals:
    # Check if file has unusually few or many items
    if file_data['items_count'] == 0:
        print(f"  WARNING: {file_data['filename']} has NO items!")
    elif file_data['items_count'] == 1:
        print(f"  WARNING: {file_data['filename']} has only 1 item (might be incomplete)")

# Save detailed results
import json
with open('facebook_totals_analysis.json', 'w', encoding='utf-8') as f:
    json.dump({
        'expected_total': EXPECTED_TOTAL,
        'actual_total': overall_total,
        'difference': overall_total - EXPECTED_TOTAL,
        'files': file_totals,
        'all_items': all_items
    }, f, ensure_ascii=False, indent=2)

print("\nDetailed results saved to facebook_totals_analysis.json")