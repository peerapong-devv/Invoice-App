#!/usr/bin/env python3
"""Test fixed Facebook parser"""

import os
import sys
import fitz
from facebook_parser_fixed import parse_facebook_invoice

sys.stdout.reconfigure(encoding='utf-8')

# Expected total from user
EXPECTED_TOTAL = 12831605.92

print("="*80)
print("TESTING FIXED FACEBOOK PARSER")
print("="*80)
print(f"Expected total: {EXPECTED_TOTAL:,.2f}")
print("="*80)

# Test all Facebook files
invoice_dir = os.path.join('..', 'Invoice for testing')
facebook_files = sorted([f for f in os.listdir(invoice_dir) if f.startswith('24') and f.endswith('.pdf')])

print(f"\nProcessing {len(facebook_files)} Facebook invoice files...")

all_items = []
excluded_count = 0

for idx, filename in enumerate(facebook_files):
    filepath = os.path.join(invoice_dir, filename)
    
    # Read text
    with fitz.open(filepath) as doc:
        text_content = ""
        for page in doc:
            text_content += page.get_text()
    
    # Parse
    items = parse_facebook_invoice(text_content, filename)
    
    if len(items) == 0 and '246952155' in filename:
        excluded_count += 1
        print(f"[{idx+1:2d}/{len(facebook_files)}] {filename}: EXCLUDED")
    else:
        # Calculate file total
        file_total = sum(item['amount'] for item in items)
        all_items.extend(items)
        print(f"[{idx+1:2d}/{len(facebook_files)}] {filename}: {len(items)} items, Total: {file_total:,.2f}")

# Calculate overall total
overall_total = sum(item['amount'] for item in all_items)

print("\n" + "="*80)
print("RESULTS")
print("="*80)
print(f"Total files processed: {len(facebook_files)}")
print(f"Files excluded: {excluded_count}")
print(f"Total items extracted: {len(all_items)}")
print(f"Overall total: {overall_total:,.2f}")
print(f"Expected total: {EXPECTED_TOTAL:,.2f}")
print(f"Difference: {overall_total - EXPECTED_TOTAL:,.2f}")

if abs(overall_total - EXPECTED_TOTAL) < 5:
    print("\n✓ SUCCESS: Total matches expected amount (within rounding tolerance)")
else:
    print("\n✗ ERROR: Total does not match expected amount")