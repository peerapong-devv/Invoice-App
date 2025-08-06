#!/usr/bin/env python3
"""Test pdfplumber parser with problematic Google invoices"""

from google_parser_pdfplumber import parse_google_invoice
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Test files that should have multiple items
test_files = [
    ('5297692778.pdf', 3),    # Extreme fragmentation
    ('5297692787.pdf', 8),    # Extreme fragmentation
    ('5298156820.pdf', 11),   # Mixed fragmentation
    ('5298248238.pdf', 7),    # Table format
]

print("Testing Google parser with pdfplumber...")
print("="*80)

for filename, expected_items in test_files:
    filepath = f'../Invoice for testing/{filename}'
    print(f"\nTesting {filename} (expected {expected_items} items)")
    print("-"*40)
    
    try:
        items = parse_google_invoice(filepath, filename)
        print(f"Found {len(items)} items:")
        
        for item in items:
            desc = item['description']
            if len(desc) > 50:
                desc = desc[:47] + '...'
            print(f"  Line {item['line_number']}: {desc} = {item['amount']:,.2f}")
        
        total = sum(item['amount'] for item in items)
        print(f"\nTotal: {total:,.2f}")
        
        if len(items) == expected_items:
            print("✓ PASSED")
        else:
            print(f"✗ FAILED - Expected {expected_items} items")
            
    except Exception as e:
        print(f"ERROR: {e}")