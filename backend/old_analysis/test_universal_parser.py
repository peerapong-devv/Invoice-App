#!/usr/bin/env python3
"""Test universal parser directly"""

import os
import sys
import fitz
from google_parser_universal import parse_google_invoice

sys.stdout.reconfigure(encoding='utf-8')

def test_file(filename):
    """Test a specific file"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Testing: {filename}")
    print('='*80)
    
    # Read text
    with fitz.open(filepath) as doc:
        text_content = ""
        for page in doc:
            text_content += page.get_text()
    
    # Parse with filepath
    items = parse_google_invoice(text_content, filepath)
    
    print(f"Extracted {len(items)} items:")
    
    total = 0
    for item in items:
        desc = item['description'][:60] + '...' if len(item['description']) > 60 else item['description']
        print(f"\n{item['line_number']}. {desc}")
        print(f"   Amount: {item['amount']:,.2f}")
        
        total += item['amount']
    
    print(f"\nTotal: {total:,.2f}")
    
    return len(items), total

# Test specific files
test_files = [
    '5297692778.pdf',  # Should have 4 items
    '5297692787.pdf',  # Should have 13 items
    '5298156820.pdf',  # Should have many items
]

for file in test_files:
    count, total = test_file(file)