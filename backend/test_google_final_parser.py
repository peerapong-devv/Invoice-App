#!/usr/bin/env python3
"""Test Google final parser"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from google_parser_final_100 import parse_google_invoice

# Test files
test_files = [
    ('5297692778.pdf', 3, 18482.50),
    ('5297692787.pdf', 10, 29304.33),
    ('5300624442.pdf', 1, 214728.05),
    ('5297736216.pdf', 1, 199789.31)
]

total_amount = 0
total_items = 0

for filename, expected_items, expected_total in test_files:
    print(f"\nTesting {filename}")
    print("-" * 40)
    
    # Read file
    filepath = f'../Invoice for testing/{filename}'
    try:
        import fitz
        with fitz.open(filepath) as doc:
            text = ''
            for page in doc:
                text += page.get_text()
        
        # Parse invoice
        items = parse_google_invoice(text, filename)
        
        print(f"Found {len(items)} items (expected {expected_items})")
        
        if items:
            file_total = items[0]['total']  # All items have same total
            print(f"Total: {file_total:,.2f} (expected {expected_total:,.2f})")
            
            total_amount += file_total
            total_items += len(items)
            
            # Show items
            for item in items[:3]:  # Show first 3 items
                print(f"  Line {item['line_number']}: {item['description'][:60]}... = {item['amount']:,.2f}")
            if len(items) > 3:
                print(f"  ... and {len(items) - 3} more items")
        
    except Exception as e:
        print(f"Error: {e}")

print(f"\n{'='*60}")
print(f"Total items processed: {total_items}")
print(f"Total amount: {total_amount:,.2f}")