#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze Google invoice structure"""

import fitz
import sys

# Set output encoding
sys.stdout.reconfigure(encoding='utf-8')

# Read and analyze the structure of a Google invoice with known line items
test_file = '../Invoice for testing/5297692778.pdf'
with fitz.open(test_file) as doc:
    print(f'Analyzing invoice 5297692778 - Total pages: {len(doc)}')
    
    # Get all text
    full_text = ''
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()
        full_text += page_text
        
        print(f'\n=== PAGE {page_num + 1} ===')
        lines = page_text.split('\n')
        
        # Look for pk| patterns
        pk_found = False
        for i, line in enumerate(lines):
            if 'pk' in line.lower() and '|' in line:
                pk_found = True
                print(f'Found pk| pattern at line {i}: {line}')
                # Check nearby lines for amounts
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    if j != i:
                        print(f'  {j}: {lines[j]}')
        
        if not pk_found and page_num > 0:
            # Look for line items in detail pages
            print('Looking for line item patterns...')
            for i, line in enumerate(lines):
                # Check for amount patterns
                if line.strip() and any(c.isdigit() for c in line):
                    # Check if it looks like an amount
                    import re
                    if re.match(r'^[\s\-]*\d{1,3}(?:,\d{3})*\.?\d*\s*$', line.strip()):
                        print(f'Potential amount at line {i}: {line}')
                        # Show context
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            if j != i:
                                print(f'  {j}: {lines[j][:100]}')
    
    # Check for specific patterns we expect
    print('\n=== SEARCHING FOR EXPECTED PATTERNS ===')
    expected_patterns = [
        'pk|40109|SDH_pk_th-single-detached-house-apitown-phitsanulok',
        '31728.38',
        '18276.77',
        '271.85',
        '31,728.38',
        '18,276.77'
    ]
    
    for pattern in expected_patterns:
        if pattern in full_text:
            print(f'✓ Found: {pattern}')
            # Find location
            idx = full_text.find(pattern)
            context = full_text[max(0, idx-100):idx+100]
            print(f'  Context: ...{context}...')
        else:
            print(f'✗ NOT Found: {pattern}')