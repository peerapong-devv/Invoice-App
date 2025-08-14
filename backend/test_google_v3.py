#!/usr/bin/env python3
"""Test Google Parser V3"""

import os
import sys
from google_parser_v3 import parse_google_invoice

sys.stdout.reconfigure(encoding='utf-8')

# Problem files
test_files = {
    '5297692778.pdf': 'Should be AP with pk| fields (18,550.72)',
    '5297692790.pdf': 'Should be -6,284.42 total (4 negative items)',
    '5297785878.pdf': 'Should have only 1 line with -1.66',
    '5297735036.pdf': 'Non-AP with different descriptions'
}

invoice_dir = os.path.join('..', 'Invoice for testing')

print("TESTING GOOGLE PARSER V3")
print("="*80)

for filename, expected in test_files.items():
    filepath = os.path.join(invoice_dir, filename)
    print(f"\n{filename}: {expected}")
    
    # Parse with V3 parser
    items = parse_google_invoice('', filepath)
    
    if items:
        total = sum(item['amount'] for item in items)
        print(f"  ✓ Invoice type: {items[0]['invoice_type']}")
        print(f"  ✓ Total items: {len(items)}")
        print(f"  ✓ Total amount: {total:,.2f}")
        
        # Check AP fields
        ap_items = [item for item in items if item.get('agency') == 'pk']
        if ap_items:
            print(f"  ✓ AP items: {len(ap_items)}")
            print(f"    First AP item:")
            print(f"      Agency: {ap_items[0].get('agency')}")
            print(f"      Project ID: {ap_items[0].get('project_id')}")
        
        # Show all items
        print(f"  Line items:")
        for item in items[:10]:  # Show first 10
            desc = item.get('description', '')[:50]
            print(f"    {item['line_number']}. {item['amount']:>10,.2f} - {desc}...")
            if item.get('agency'):
                print(f"       [AP] Agency: {item['agency']}, Project: {item.get('project_id')}")
    else:
        print("  ✗ ERROR: No items extracted!")

# Test all Google files
print("\n" + "="*80)
print("TESTING ALL GOOGLE FILES")
print("="*80)

google_files = sorted([f for f in os.listdir(invoice_dir) if f.startswith('5') and f.endswith('.pdf')])
total_amount = 0
total_items = 0
problem_files = []

for filename in google_files[:10]:  # Test first 10
    filepath = os.path.join(invoice_dir, filename)
    items = parse_google_invoice('', filepath)
    
    if items:
        file_total = sum(item['amount'] for item in items)
        total_amount += file_total
        total_items += len(items)
        
        if len(items) == 1 and abs(file_total) > 1000:
            problem_files.append((filename, file_total, "Only 1 item for large amount"))
    else:
        problem_files.append((filename, 0, "No items extracted"))

print(f"\nProcessed {len(google_files[:10])} files")
print(f"Total items: {total_items}")
print(f"Total amount: {total_amount:,.2f}")
print(f"Average items per file: {total_items / 10:.2f}")

if problem_files:
    print(f"\nProblem files ({len(problem_files)}):")
    for filename, amount, issue in problem_files[:5]:
        print(f"  {filename}: {issue} (amount: {amount:,.2f})")