#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Google universal parser"""

import fitz
from google_parser_final_universal import parse_google_invoice
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Test on various invoice types
test_files = [
    # Fragmented text invoices
    ('5297692778.pdf', 3),   # Should extract 3 items
    ('5297692787.pdf', 8),   # Should extract 8 items
    
    # Table format invoices
    ('5298156820.pdf', 11),  # Should extract 11 items
    ('5297692799.pdf', 6),   # Should extract 6 items
    ('5298248238.pdf', 7),   # Should extract 7 items
]

for filename, expected_items in test_files:
    filepath = f'../Invoice for testing/{filename}'
    print(f"\n{'='*80}")
    print(f"Testing {filename} (expected {expected_items} items)")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        text = ''
        for page in doc:
            text += page.get_text()
    
    items = parse_google_invoice(text, filename)
    print(f'Found {len(items)} items:')
    
    for item in items:
        desc = item['description']
        if len(desc) > 60:
            desc = desc[:57] + '...'
        print(f'  Line {item["line_number"]}: {desc} = {item["amount"]:,.2f}')
        if item.get('project_id'):
            print(f'    Project: {item.get("project_id")} - {item.get("project_name", "N/A")}, Objective: {item.get("objective", "N/A")}')
    
    total = sum(item['amount'] for item in items)
    print(f'\nTotal: {total:,.2f}')
    
    # Check result
    if len(items) == expected_items:
        print('✓ PASSED - Correct number of items')
    else:
        print(f'✗ FAILED - Expected {expected_items} items, got {len(items)}')