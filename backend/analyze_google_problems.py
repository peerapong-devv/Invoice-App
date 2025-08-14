#!/usr/bin/env python3
"""Analyze specific Google invoice problems"""

import os
import sys
import fitz
import re

sys.stdout.reconfigure(encoding='utf-8')

# Problems identified by user
problems = {
    '5297692778.pdf': 'AP invoice but no AP fields extracted',
    '5297692787.pdf': 'Same as 5297692778',
    '5297693015.pdf': 'Same as 5297692778', 
    '5297732883.pdf': 'Same as 5297692778',
    '5297742275.pdf': 'Same as 5297692778',
    '5297830454.pdf': 'Same as 5297692778',
    '5297969160.pdf': 'Same as 5297692778',
    '5297692790.pdf': 'Wrong total, missing 1 line (should be -6,284.42)',
    '5297692799.pdf': 'Same as 5297692778, missing 1 line',
    '5297735036.pdf': 'Non-AP correct but all descriptions are same',
    '5297736216.pdf': 'Same as 5297735036',
    '5297785878.pdf': 'Should have only 1 line with -1.66, but getting 6 lines'
}

invoice_dir = os.path.join('..', 'Invoice for testing')

# First, let's check AP invoices to see pk| patterns
print("="*80)
print("CHECKING AP INVOICES FOR pk| PATTERNS")
print("="*80)

ap_files = ['5297692778.pdf', '5297692787.pdf', '5297693015.pdf', '5297732883.pdf', 
            '5297742275.pdf', '5297830454.pdf', '5297969160.pdf', '5297692799.pdf']

for filename in ap_files[:3]:  # Check first 3
    filepath = os.path.join(invoice_dir, filename)
    print(f"\n{filename}:")
    
    with fitz.open(filepath) as doc:
        # Check all pages for pk| pattern
        pk_found = False
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            if 'pk|' in text:
                pk_found = True
                print(f"  Found pk| on page {page_num + 1}")
                
                # Extract pk patterns
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if 'pk|' in line:
                        print(f"    Line {i}: {line.strip()[:100]}...")
                        # Check next few lines
                        for j in range(1, 4):
                            if i + j < len(lines) and lines[i+j].strip():
                                print(f"      +{j}: {lines[i+j].strip()[:80]}...")
        
        if not pk_found:
            print("  NO pk| pattern found!")

# Check specific problem files
print("\n" + "="*80)
print("CHECKING SPECIFIC PROBLEM FILES")
print("="*80)

# Check 5297692790.pdf - should be -6,284.42
print("\n5297692790.pdf (should be -6,284.42):")
filepath = os.path.join(invoice_dir, '5297692790.pdf')
with fitz.open(filepath) as doc:
    if len(doc) >= 2:
        page2 = doc[1]
        text = page2.get_text()
        lines = text.split('\n')
        
        # Find all amounts
        amounts = []
        for i, line in enumerate(lines):
            amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})', line)
            if amount_match:
                amount = float(amount_match.group(1).replace(',', ''))
                if abs(amount) > 0.01 and abs(amount) < 100000:
                    amounts.append((i, line.strip(), amount))
        
        print(f"  Found {len(amounts)} amounts on page 2:")
        total = 0
        for idx, (line_num, line_text, amount) in enumerate(amounts[:10]):
            print(f"    {idx+1}. Line {line_num}: {amount:,.2f}")
            total += amount
        print(f"  Total: {total:,.2f} (Expected: -6,284.42)")

# Check 5297785878.pdf - should have only 1 line with -1.66
print("\n5297785878.pdf (should have only 1 line with -1.66):")
filepath = os.path.join(invoice_dir, '5297785878.pdf')
with fitz.open(filepath) as doc:
    print(f"  Pages: {len(doc)}")
    
    # Check all pages
    all_amounts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split('\n')
        
        # Look for amounts
        for i, line in enumerate(lines):
            if '-1.66' in line or '1.66' in line:
                print(f"  Page {page_num + 1}, Line {i}: {line.strip()}")
            
            # Also check for other amounts
            amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})', line)
            if amount_match:
                amount = float(amount_match.group(1).replace(',', ''))
                if 0.01 < abs(amount) < 100:  # Small amounts
                    all_amounts.append((page_num + 1, i, amount, line.strip()[:60]))
    
    print(f"\n  All small amounts found:")
    for page, line_num, amount, text in all_amounts:
        print(f"    Page {page}, Line {line_num}: {amount:,.2f} - {text}")

# Check 5297735036.pdf - descriptions
print("\n5297735036.pdf (Non-AP with same descriptions):")
filepath = os.path.join(invoice_dir, '5297735036.pdf')
with fitz.open(filepath) as doc:
    if len(doc) >= 2:
        page2 = doc[1]
        text = page2.get_text()
        lines = text.split('\n')
        
        print("  Looking for line item patterns on page 2:")
        # Look for campaign/description patterns
        for i in range(len(lines)):
            line = lines[i].strip()
            # Check for patterns that might be descriptions
            if any(pattern in line for pattern in ['Campaign', 'แคมเปญ', '|', 'การคลิก', 'การแสดงผล']):
                print(f"    Line {i}: {line[:80]}...")
                # Check if next line has amount
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.search(r'\d+\.\d{2}', next_line):
                        print(f"      Amount: {next_line}")