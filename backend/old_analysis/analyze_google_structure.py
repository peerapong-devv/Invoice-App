#!/usr/bin/env python3
"""Analyze Google invoice structure to understand how to extract all line items"""

import fitz
import re
import os

def analyze_google_invoice(filename):
    """Analyze a Google invoice to understand its structure"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\nAnalyzing: {filename}")
    print("="*80)
    
    with fitz.open(filepath) as doc:
        for page_num, page in enumerate(doc):
            text = page.get_text()
            lines = text.split('\n')
            
            print(f"\nPage {page_num + 1}:")
            print("-"*40)
            
            # Track what we find
            line_items = []
            in_table = False
            current_item = {}
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Look for table indicators
                if 'รายการ' in line or 'Description' in line:
                    in_table = True
                    print(f"Found table header at line {i}: {line}")
                
                # Look for amounts (numbers with 2 decimals)
                amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})', line)
                if amount_match and in_table:
                    amount = float(amount_match.group(1).replace(',', ''))
                    
                    # Look back for description
                    desc_lines = []
                    for j in range(max(0, i-10), i):
                        prev_line = lines[j].strip()
                        if prev_line and not re.match(r'^[-\d,.\s]+$', prev_line):
                            desc_lines.append(prev_line)
                    
                    if desc_lines:
                        line_items.append({
                            'description': ' '.join(desc_lines[-3:]),  # Last 3 non-empty lines
                            'amount': amount,
                            'line_pos': i
                        })
            
            # Print findings
            print(f"\nFound {len(line_items)} potential line items:")
            for idx, item in enumerate(line_items[:10]):  # First 10
                desc = item['description'][:60] + '...' if len(item['description']) > 60 else item['description']
                print(f"{idx+1}. {desc}")
                print(f"   Amount: {item['amount']:,.2f} (line {item['line_pos']})")
            
            if len(line_items) > 10:
                print(f"... and {len(line_items) - 10} more items")

# Analyze different types of Google invoices
test_files = [
    '5297736216.pdf',  # AP with only 1 item extracted (should have many)
    '5297692778.pdf',  # Has hardcoded pattern (3 items)
    '5298156820.pdf',  # Large amount
    '5300624442.pdf',  # Another large one
]

for f in test_files:
    if os.path.exists(os.path.join('..', 'Invoice for testing', f)):
        analyze_google_invoice(f)