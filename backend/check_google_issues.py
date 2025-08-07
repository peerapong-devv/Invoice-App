#!/usr/bin/env python3
"""Check specific Google parser issues mentioned by user"""

import os
import sys
import fitz

sys.stdout.reconfigure(encoding='utf-8')

# Files with specific issues
issues = {
    '5297692778.pdf': {
        'problem': 'Has 3 line items but parser extracts 4 (includes total 18,482.50)',
        'expected_items': 3
    },
    '5297692787.pdf': {
        'problem': 'Correct item count but missing AP fields extraction',
        'expected_items': 8
    },
    '5297732883.pdf': {
        'problem': 'Missing fee from last page',
        'has_fee': True
    },
    '5297786049.pdf': {
        'problem': 'Missing fee from last page',
        'has_fee': True
    }
}

invoice_dir = os.path.join('..', 'Invoice for testing')

for filename, info in issues.items():
    filepath = os.path.join(invoice_dir, filename)
    
    print(f"\n{'='*80}")
    print(f"Checking: {filename}")
    print(f"Issue: {info['problem']}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        num_pages = len(doc)
        print(f"Pages: {num_pages}")
        
        # Check last page for fees
        if info.get('has_fee'):
            last_page = doc[num_pages - 1]
            text = last_page.get_text()
            lines = text.split('\n')
            
            print(f"\nLast page content (looking for fees):")
            fee_found = False
            for i, line in enumerate(lines):
                if 'ค่าธรรมเนียม' in line or 'fee' in line.lower():
                    fee_found = True
                    print(f"  Line {i}: {line}")
                    # Show next few lines
                    for j in range(1, 4):
                        if i + j < len(lines):
                            print(f"  Line {i+j}: {lines[i+j].strip()}")
            
            if not fee_found:
                print("  No fee text found on last page")
        
        # Check page 2 for line items
        if num_pages > 1:
            page2 = doc[1]
            text = page2.get_text()
            lines = text.split('\n')
            
            print(f"\nPage 2 line items:")
            # Look for amounts
            amounts = []
            for i, line in enumerate(lines):
                import re
                amount_match = re.search(r'([-]?[\d,]+\.\d{2})', line)
                if amount_match:
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                        if 0.01 <= abs(amount) <= 1000000:
                            amounts.append((i, line.strip(), amount))
                    except:
                        pass
            
            print(f"  Found {len(amounts)} amounts on page 2:")
            for idx, (line_num, line_text, amount) in enumerate(amounts[:10]):
                print(f"    {idx+1}. Line {line_num}: {amount:,.2f} - {line_text[:50]}...")
            
            # Check if 18,482.50 appears (the problematic total)
            if filename == '5297692778.pdf':
                print("\n  Looking for 18,482.50 specifically:")
                for i, line in enumerate(lines):
                    if '18,482.50' in line or '18482.50' in line:
                        print(f"    Found at line {i}: {line.strip()}")
                        # Context
                        for j in range(max(0, i-3), min(i+3, len(lines))):
                            if j != i:
                                print(f"      {j}: {lines[j].strip()}")
        
        # Check for AP patterns
        if filename == '5297692787.pdf':
            print(f"\nChecking for AP patterns (pk|):")
            all_text = ""
            for page in doc:
                all_text += page.get_text()
            
            import re
            pk_patterns = re.findall(r'pk\|[^\n]+', all_text)
            print(f"  Found {len(pk_patterns)} pk| patterns:")
            for i, pattern in enumerate(pk_patterns[:5]):
                print(f"    {i+1}. {pattern[:80]}...")
            
            # Check specific line items on page 2
            if num_pages > 1:
                page2 = doc[1]
                text = page2.get_text()
                lines = text.split('\n')
                
                print("\n  Checking line item structure on page 2:")
                # Look for pattern: description | amount
                for i in range(len(lines)):
                    if 'pk|' in lines[i]:
                        print(f"\n    Line {i}: {lines[i].strip()}")
                        # Check next lines for amount
                        for j in range(1, 5):
                            if i + j < len(lines):
                                next_line = lines[i+j].strip()
                                if next_line:
                                    print(f"      +{j}: {next_line}")