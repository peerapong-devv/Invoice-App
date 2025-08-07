#!/usr/bin/env python3
"""Test the comprehensive Google parser"""

import os
import sys
from google_parser_comprehensive import parse_google_invoice

sys.stdout.reconfigure(encoding='utf-8')

def test_parser(filename):
    """Test the parser on a specific file"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Testing: {filename}")
    print('='*80)
    
    # Parse using the comprehensive parser
    items = parse_google_invoice(filepath, filename)
    
    # Show results
    print(f"Extracted {len(items)} items:")
    
    total = 0
    for item in items:
        desc = item['description'][:60] + '...' if len(item['description']) > 60 else item['description']
        print(f"\n{item['line_number']}. {desc}")
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
    
    # Check against expected
    expected_totals = {
        '5298156820.pdf': 1603456.84,
        '5297692778.pdf': 36965.00,
        '5300624442.pdf': 429456.10,
        '5297692787.pdf': 56626.86
    }
    
    if filename in expected_totals:
        expected = expected_totals[filename]
        diff = abs(total - expected)
        if diff < 0.01:
            print(f"✓ Total matches expected: {expected:,.2f}")
        else:
            print(f"✗ Total differs from expected: {expected:,.2f} (diff: {diff:,.2f})")
    
    return len(items), total

# Test on various files
test_files = [
    '5298156820.pdf',  # Large with multiple items
    '5297692778.pdf',  # Fragmented text with pk| patterns
    '5300624442.pdf',  # Different format
    '5297692787.pdf',  # Another test case
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