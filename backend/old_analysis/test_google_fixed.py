#!/usr/bin/env python3
"""Test the fixed Google parser"""

import os
import sys
from google_parser_fixed import parse_google_invoice

sys.stdout.reconfigure(encoding='utf-8')

def test_parser(filename):
    """Test the parser on a specific file"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Testing: {filename}")
    print('='*80)
    
    # Parse using the new parser
    items = parse_google_invoice('dummy', filepath)  # Pass filepath as filename
    
    # Show results
    print(f"Extracted {len(items)} items:")
    
    total = 0
    for item in items:
        print(f"\n{item['line_number']}. {item['description'][:80]}...")
        if item.get('campaign_code'):
            print(f"   Campaign Code: {item['campaign_code']}")
        print(f"   Amount: {item['amount']:,.2f}")
        print(f"   Type: {item['invoice_type']}")
        if item.get('project_name'):
            print(f"   Project: {item.get('project_name')}")
        if item.get('objective'):
            print(f"   Objective: {item['objective']}")
        
        total += item['amount']
    
    print(f"\nCalculated Total: {total:,.2f}")
    
    return len(items), total

# Test on various files
test_files = [
    '5298156820.pdf',  # Should have multiple items
    '5297692778.pdf',  # Has 3 items in hardcoded
    '5300624442.pdf',  # Another multi-item
    '5297692787.pdf',  # Currently only 1 item
]

summary = []
for file in test_files:
    filepath = os.path.join('..', 'Invoice for testing', file)
    if os.path.exists(filepath):
        count, total = test_parser(file)
        summary.append((file, count, total))

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
for file, count, total in summary:
    print(f"{file}: {count} items, Total: {total:,.2f}")