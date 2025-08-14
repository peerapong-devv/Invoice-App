#!/usr/bin/env python3
"""Test if Google parser now correctly handles AP invoices"""

import os
import sys
import json
from google_parser_fixed_final import parse_google_invoice

sys.stdout.reconfigure(encoding='utf-8')

# Test files with AP issues
test_files = [
    '5297692778.pdf',
    '5297692790.pdf', 
    '5297785878.pdf',
    '5297735036.pdf'
]

invoice_dir = os.path.join('..', 'Invoice for testing')
results = {}

print("Testing Google Parser AP Fix")
print("="*80)

for filename in test_files:
    filepath = os.path.join(invoice_dir, filename)
    print(f"\nTesting {filename}:")
    
    # Parse with updated parser
    with open(filepath, 'rb') as f:
        items = parse_google_invoice('', filepath)
    
    total = sum(item['amount'] for item in items)
    ap_items = [item for item in items if item.get('agency') == 'pk']
    
    print(f"  Invoice type: {items[0].get('invoice_type') if items else 'Unknown'}")
    print(f"  Total items: {len(items)}")
    print(f"  Total amount: {total:,.2f}")
    print(f"  AP items (with pk): {len(ap_items)}")
    
    if ap_items:
        print(f"  First AP item:")
        print(f"    Agency: {ap_items[0].get('agency')}")
        print(f"    Project ID: {ap_items[0].get('project_id')}")
        print(f"    Description: {ap_items[0].get('description', '')[:80]}...")
    
    results[filename] = {
        'invoice_type': items[0].get('invoice_type') if items else 'Unknown',
        'total_items': len(items),
        'total_amount': total,
        'ap_items': len(ap_items),
        'has_pk_fields': len(ap_items) > 0
    }

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

for filename, data in results.items():
    status = "✓" if (data['invoice_type'] == 'AP' and data['has_pk_fields']) or (data['invoice_type'] == 'Non-AP' and not data['has_pk_fields']) else "✗"
    print(f"{status} {filename}: {data['invoice_type']}, {data['total_items']} items, {data['total_amount']:,.2f} THB")