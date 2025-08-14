#!/usr/bin/env python3
"""Test specific Google problem files"""

import os
import sys
from google_parser_final_fixed import parse_google_invoice

sys.stdout.reconfigure(encoding='utf-8')

# Problem files
test_files = {
    '5297692778.pdf': 'Should be AP with pk| fields',
    '5297692790.pdf': 'Should be -6,284.42 total',
    '5297785878.pdf': 'Should have only 1 line with -1.66',
    '5297735036.pdf': 'Non-AP with different descriptions'
}

invoice_dir = os.path.join('..', 'Invoice for testing')

print("TESTING GOOGLE PROBLEM FILES")
print("="*80)

for filename, expected in test_files.items():
    filepath = os.path.join(invoice_dir, filename)
    print(f"\n{filename}: {expected}")
    
    # Parse with new parser
    items = parse_google_invoice('', filepath)
    
    if items:
        total = sum(item['amount'] for item in items)
        print(f"  Invoice type: {items[0]['invoice_type']}")
        print(f"  Total items: {len(items)}")
        print(f"  Total amount: {total:,.2f}")
        
        # Check AP fields
        ap_items = [item for item in items if item.get('agency') == 'pk']
        if ap_items:
            print(f"  AP items: {len(ap_items)}")
            print(f"  First AP item:")
            print(f"    Agency: {ap_items[0].get('agency')}")
            print(f"    Project ID: {ap_items[0].get('project_id')}")
        
        # Show all items
        print(f"  Line items:")
        for item in items:
            desc = item.get('description', '')[:60]
            print(f"    {item['line_number']}. {item['amount']:>10,.2f} - {desc}...")
            if item.get('agency'):
                print(f"       [AP] Agency: {item['agency']}, Project: {item.get('project_id')}")
    else:
        print("  ERROR: No items extracted!")

# Test more AP files
print("\n" + "="*80)
print("TESTING MORE AP FILES")
print("="*80)

ap_files = ['5297692787.pdf', '5297693015.pdf', '5297732883.pdf']
for filename in ap_files:
    filepath = os.path.join(invoice_dir, filename)
    items = parse_google_invoice('', filepath)
    
    if items:
        total = sum(item['amount'] for item in items)
        ap_count = len([item for item in items if item.get('agency') == 'pk'])
        print(f"\n{filename}: Type={items[0]['invoice_type']}, Items={len(items)}, Total={total:,.2f}, AP items={ap_count}")