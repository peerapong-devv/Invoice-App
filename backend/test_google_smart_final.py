#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Google smart final parser"""

import fitz
from google_parser_smart_final import parse_google_invoice
import sys

# Set output encoding
sys.stdout.reconfigure(encoding='utf-8')

# Test with the three invoices that have known line items
test_invoices = [
    {'file': '5297692778.pdf', 'expected': 3, 'total': 50277.00},
    {'file': '5297692787.pdf', 'expected': 8, 'total': 18875.62},
    {'file': '5297692790.pdf', 'expected': 4, 'total': -6284.42}
]

for test in test_invoices:
    test_file = f'../Invoice for testing/{test["file"]}'
    print(f"\nTesting {test['file']} (expected {test['expected']} items, total {test['total']:,.2f}):")
    print("="*80)
    
    with fitz.open(test_file) as doc:
        text = ''
        for page in doc:
            text += page.get_text()
    
    items = parse_google_invoice(text, test['file'])
    print(f'Found {len(items)} items:')
    
    total = 0
    for item in items:
        desc = item['description']
        if len(desc) > 60:
            desc = desc[:57] + '...'
        print(f'  Line {item["line_number"]}: {desc} = {item["amount"]:,.2f}')
        if item.get('project_id'):
            print(f'    Project: {item["project_id"]} - {item.get("project_name", "N/A")}')
            print(f'    Objective: {item.get("objective", "N/A")}')
        total += item['amount']
    
    print(f'\nCalculated Total: {total:,.2f}')
    print(f'Expected Total: {test["total"]:,.2f}')
    
    if len(items) == test['expected']:
        print('✓ PASSED - Correct number of line items')
    else:
        print(f'✗ FAILED - Expected {test["expected"]} items, got {len(items)}')
    
    if abs(total - test['total']) < 1.0:
        print('✓ PASSED - Total matches expected')
    else:
        print(f'✗ FAILED - Total mismatch')