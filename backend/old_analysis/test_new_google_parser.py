#!/usr/bin/env python3
"""Test the new Google parser that extracts all line items"""

import os
import sys
import fitz
from google_parser_complete_line_items import parse_google_invoice

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

def test_parser(filename):
    """Test the parser on a specific file"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Testing: {filename}")
    print('='*80)
    
    # Read PDF
    with fitz.open(filepath) as doc:
        text = ''
        for page in doc:
            text += page.get_text()
    
    # Parse
    items = parse_google_invoice(text, filename)
    
    # Show results
    print(f"Extracted {len(items)} items:")
    
    total = 0
    for item in items:
        print(f"\n{item['line_number']}. {item['description'][:80]}...")
        print(f"   Amount: {item['amount']:,.2f}")
        print(f"   Type: {item['invoice_type']}")
        if item.get('project_id'):
            print(f"   Project: {item.get('project_id')} - {item.get('project_name')}")
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
    if os.path.exists(os.path.join('..', 'Invoice for testing', file)):
        count, total = test_parser(file)
        summary.append((file, count, total))

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
for file, count, total in summary:
    print(f"{file}: {count} items, Total: {total:,.2f}")