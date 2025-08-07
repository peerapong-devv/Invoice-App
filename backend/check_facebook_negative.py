#!/usr/bin/env python3
"""Check Facebook invoices for negative amounts"""

import os
import sys
import fitz

sys.stdout.reconfigure(encoding='utf-8')

# Check specific files mentioned by user
files_to_check = {
    '246543739.pdf': {
        'expected_total': 1985559.44,
        'negative_lines': [139, 108, 91, 16]
    },
    '246546622.pdf': {
        'expected_total': None,
        'negative_lines': []  # User mentioned it has negative lines
    }
}

invoice_dir = os.path.join('..', 'Invoice for testing')

for filename, info in files_to_check.items():
    filepath = os.path.join(invoice_dir, filename)
    
    print(f"\n{'='*80}")
    print(f"Checking: {filename}")
    if info['expected_total']:
        print(f"Expected total: {info['expected_total']:,.2f}")
    print(f"Looking for negative amounts at lines: {info['negative_lines']}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            lines = text.split('\n')
            
            print(f"\n--- PAGE {page_num + 1} ---")
            
            # Look for ar@meta.com marker
            ar_meta_line = -1
            for i, line in enumerate(lines):
                if 'ar@meta.com' in line:
                    ar_meta_line = i
                    print(f"Found ar@meta.com at line {i}")
                    break
            
            if ar_meta_line > 0:
                # Check the specific lines mentioned
                print("\nChecking for negative amounts:")
                
                # Show context around the mentioned line numbers
                for line_num in info['negative_lines']:
                    if line_num < len(lines):
                        print(f"\nAround line {line_num}:")
                        for j in range(max(0, line_num-3), min(line_num+3, len(lines))):
                            line_content = lines[j].strip()
                            prefix = ">>>" if j == line_num else "   "
                            print(f"{prefix} {j:3d}: {line_content}")
                
                # Also search for any negative amounts
                print("\nSearching for all negative amounts in the file:")
                for i, line in enumerate(lines):
                    line = line.strip()
                    # Look for negative patterns
                    if '-' in line and any(c.isdigit() for c in line):
                        # Check if it's a negative amount
                        import re
                        neg_pattern = r'-\s*[\d,]+\.?\d*'
                        if re.search(neg_pattern, line):
                            print(f"  Line {i}: {line}")
                            # Check if it's after ar@meta.com
                            if i > ar_meta_line:
                                print(f"    -> This is {i - ar_meta_line} lines after ar@meta.com")