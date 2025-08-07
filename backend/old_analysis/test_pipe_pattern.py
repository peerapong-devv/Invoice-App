#!/usr/bin/env python3
"""Test pipe pattern extraction specifically"""

import os
import sys
import fitz
import re

sys.stdout.reconfigure(encoding='utf-8')

def test_pipe_extraction(filename):
    """Test extracting items with pipe pattern"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Testing Pipe Pattern: {filename}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        # Focus on page 2 where line items are
        if len(doc) < 2:
            print("No page 2 found!")
            return
        
        page2 = doc[1]
        text = page2.get_text()
        
        # Clean text
        text = text.replace('\u200b', '')
        lines = text.split('\n')
        
        print(f"\nSearching for pipe patterns on page 2...")
        
        # Find all lines with pipe
        pipe_lines = []
        for i, line in enumerate(lines):
            if '|' in line:
                pipe_lines.append((i, line))
        
        print(f"Found {len(pipe_lines)} lines with pipe character")
        
        # Process each pipe line
        items = []
        for line_no, line in pipe_lines[:10]:  # First 10
            print(f"\nLine {line_no}: {line[:100]}...")
            
            # Split by pipe
            parts = line.split('|')
            if len(parts) >= 2:
                description = parts[0].strip()
                campaign_code = parts[1].strip()
                
                print(f"  Description: {description[:80]}...")
                print(f"  Campaign Code: {campaign_code[:50]}...")
                
                # Look for amount in same line or nearby
                amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    print(f"  Amount (same line): {amount:,.2f}")
                    items.append({
                        'description': description,
                        'campaign_code': campaign_code.replace(amount_match.group(0), '').strip(),
                        'amount': amount
                    })
                else:
                    # Look in next few lines
                    for j in range(line_no + 1, min(line_no + 5, len(lines))):
                        next_line = lines[j]
                        amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', next_line)
                        if amount_match:
                            amount = float(amount_match.group(1).replace(',', ''))
                            print(f"  Amount (line {j}): {amount:,.2f}")
                            items.append({
                                'description': description,
                                'campaign_code': campaign_code,
                                'amount': amount
                            })
                            break
        
        # Show summary
        print(f"\n\nExtracted {len(items)} items with pipe pattern:")
        for i, item in enumerate(items):
            print(f"\n{i+1}. {item['description'][:60]}...")
            print(f"   Code: {item['campaign_code']}")
            print(f"   Amount: {item['amount']:,.2f}")
        
        total = sum(item['amount'] for item in items)
        print(f"\nTotal: {total:,.2f}")

# Test on a file
test_pipe_extraction('5298156820.pdf')