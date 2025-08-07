#!/usr/bin/env python3
"""Extract line items from Google invoices by studying the pattern"""

import fitz
import re
import os
import sys

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

def analyze_and_extract(filename):
    """Analyze and extract line items from Google invoice"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\nAnalyzing: {filename}")
    print("="*80)
    
    with fitz.open(filepath) as doc:
        all_text = ""
        for page in doc:
            all_text += page.get_text()
        
        # Clean text from zero-width spaces
        clean_text = all_text.replace('\u200b', '')
        
        # Split into lines
        lines = clean_text.split('\n')
        
        # Find the main table section
        table_start = -1
        table_end = -1
        
        for i, line in enumerate(lines):
            # Look for table headers in Thai or English
            if 'รายการ' in line or 'Description' in line or 'รายละเอียด' in line:
                table_start = i
                print(f"Found table start at line {i}: {line.strip()}")
            
            # Look for total section
            if 'ยอดรวม' in line or 'Total' in line or 'จำนวนเงินรวม' in line:
                if table_start > 0 and i > table_start + 5:
                    table_end = i
                    print(f"Found table end at line {i}: {line.strip()}")
                    break
        
        # Extract items between table start and end
        items = []
        
        if table_start > 0:
            i = table_start + 1
            while i < min(table_end if table_end > 0 else len(lines), len(lines)):
                line = lines[i].strip()
                
                # Look for amounts
                amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    
                    # Collect description from previous lines
                    desc_lines = []
                    j = i - 1
                    while j > table_start:
                        prev_line = lines[j].strip()
                        if not prev_line:
                            j -= 1
                            continue
                        
                        # Stop if we hit another amount
                        if re.search(r'\d+\.\d{2}', prev_line):
                            break
                        
                        desc_lines.insert(0, prev_line)
                        j -= 1
                        
                        # Stop after collecting reasonable amount of text
                        if len(' '.join(desc_lines)) > 200:
                            break
                    
                    if desc_lines or abs(amount) > 0:
                        description = ' '.join(desc_lines)
                        
                        # Clean up description
                        description = re.sub(r'\s+', ' ', description)
                        
                        items.append({
                            'description': description,
                            'amount': amount
                        })
                
                i += 1
        
        # If no table found, try alternative approach
        if not items:
            print("\nNo table structure found, trying pattern matching...")
            
            # Look for lines with amounts
            for i, line in enumerate(lines):
                amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    
                    # Skip very small amounts or page numbers
                    if abs(amount) < 0.1 or amount > 10000000:
                        continue
                    
                    # Get context
                    context = []
                    for j in range(max(0, i-5), i):
                        if lines[j].strip():
                            context.append(lines[j].strip())
                    
                    if context:
                        items.append({
                            'description': ' '.join(context[-2:]),  # Last 2 context lines
                            'amount': amount
                        })
        
        # Print results
        print(f"\nExtracted {len(items)} line items:")
        for idx, item in enumerate(items):
            desc = item['description'][:80] + '...' if len(item['description']) > 80 else item['description']
            print(f"\n{idx+1}. Amount: {item['amount']:,.2f}")
            print(f"   Description: {desc}")
        
        # Calculate total
        if items:
            total = sum(item['amount'] for item in items)
            print(f"\nCalculated Total: {total:,.2f}")
        
        return items

# Test on a file that should have multiple items
items = analyze_and_extract('5298156820.pdf')

# Also check the structure of a working hardcoded file
print("\n\n" + "="*80)
print("Checking hardcoded file for comparison:")
items2 = analyze_and_extract('5297692778.pdf')