#!/usr/bin/env python3
"""Extract line items from page 2 of Google invoices where the details are"""

import fitz
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def extract_page2_items(filename):
    """Extract line items from page 2 of Google invoice"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\nAnalyzing Page 2 of: {filename}")
    print("="*80)
    
    with fitz.open(filepath) as doc:
        if len(doc) < 2:
            print("No page 2 found!")
            return []
        
        # Get page 2 text
        page2 = doc[1]
        text = page2.get_text()
        
        # Clean and split
        text = text.replace('\u200b', '')
        lines = text.split('\n')
        
        print(f"Page 2 has {len(lines)} lines")
        
        # Look for campaign/item patterns
        items = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Pattern 1: Look for lines that might be campaign descriptions
            # These often contain pk|, campaign names, or specific patterns
            if ('pk' in line or 'Campaign' in line or '|' in line or 
                'Traffic' in line or 'Search' in line or 'Awareness' in line or
                'งานแคมเปญ' in line):
                
                # Look ahead for amount
                amount_found = False
                for j in range(i+1, min(i+10, len(lines))):
                    next_line = lines[j].strip()
                    amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', next_line)
                    
                    if amount_match:
                        amount = float(amount_match.group(1).replace(',', ''))
                        
                        # Collect all lines between description and amount
                        desc_parts = [line]
                        for k in range(i+1, j):
                            if lines[k].strip():
                                desc_parts.append(lines[k].strip())
                        
                        items.append({
                            'description': ' '.join(desc_parts),
                            'amount': amount,
                            'line': i
                        })
                        
                        i = j  # Skip to after amount
                        amount_found = True
                        break
                
                if not amount_found:
                    # Try looking for amount in the same line
                    amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
                    if amount_match:
                        amount = float(amount_match.group(1).replace(',', ''))
                        desc = line.replace(amount_match.group(0), '').strip()
                        if desc:
                            items.append({
                                'description': desc,
                                'amount': amount,
                                'line': i
                            })
            
            # Pattern 2: Look for Thai text followed by amounts
            elif any(thai in line for thai in ['ค่า', 'ภาษี', 'รวม', 'กิจกรรม', 'โฆษณา']):
                amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    desc = line.replace(amount_match.group(0), '').strip()
                    if desc and abs(amount) > 0:
                        items.append({
                            'description': desc,
                            'amount': amount,
                            'line': i
                        })
            
            i += 1
        
        # Also try to find all amounts and work backwards
        if len(items) < 3:  # If we found very few items
            print("\nTrying alternative extraction method...")
            
            amount_lines = []
            for i, line in enumerate(lines):
                amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    if 0.01 <= abs(amount) <= 10000000:  # Reasonable range
                        amount_lines.append((i, amount, line))
            
            print(f"Found {len(amount_lines)} lines with amounts")
            
            # For each amount, try to find its description
            for line_no, amount, full_line in amount_lines[:20]:  # First 20
                # Look back for description
                desc = ""
                for j in range(line_no-1, max(0, line_no-5), -1):
                    prev_line = lines[j].strip()
                    if prev_line and not re.match(r'^[\d,.-]+$', prev_line):
                        desc = prev_line + " " + desc
                        break
                
                if not desc:
                    # Use the same line
                    desc = full_line.replace(str(amount), '').replace(',', '').strip()
                
                if desc:
                    items.append({
                        'description': desc.strip(),
                        'amount': amount,
                        'line': line_no
                    })
        
        # Remove duplicates
        seen = set()
        unique_items = []
        for item in items:
            key = (item['description'][:50], item['amount'])
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        # Print results
        print(f"\nExtracted {len(unique_items)} unique line items:")
        for idx, item in enumerate(unique_items[:15]):  # First 15
            desc = item['description'][:80] + '...' if len(item['description']) > 80 else item['description']
            print(f"\n{idx+1}. Amount: {item['amount']:,.2f} (line {item['line']})")
            print(f"   Description: {desc}")
        
        if len(unique_items) > 15:
            print(f"\n... and {len(unique_items) - 15} more items")
        
        # Calculate total
        if unique_items:
            total = sum(item['amount'] for item in unique_items)
            print(f"\nCalculated Total: {total:,.2f}")
        
        return unique_items

# Test on different invoice types
test_files = [
    '5298156820.pdf',  # Large amount
    '5297692778.pdf',  # Has hardcoded pattern
    '5300624442.pdf',  # Another one
]

for file in test_files:
    if os.path.exists(os.path.join('..', 'Invoice for testing', file)):
        print("\n" + "="*80)
        items = extract_page2_items(file)