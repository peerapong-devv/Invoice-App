#!/usr/bin/env python3
"""Check single Google invoice"""

import fitz
import re

def check_invoice(filepath):
    """Extract and display all text from invoice"""
    print(f"Checking invoice: {filepath}")
    print("="*80)
    
    with fitz.open(filepath) as doc:
        full_text = ""
        for page_num, page in enumerate(doc):
            text = page.get_text()
            full_text += text
            print(f"\nPage {page_num + 1}:")
            print("-"*40)
            # Print line by line to see structure
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    # Look for amounts (numbers with decimals)
                    if re.search(r'\d+\.\d{2}', line):
                        print(f"{i:3d}: >>> {line.strip().encode('ascii', 'replace').decode('ascii')}")
                    else:
                        print(f"{i:3d}:     {line.strip().encode('ascii', 'replace').decode('ascii')}")
    
    # Look for total patterns
    print("\n\nSearching for totals:")
    print("-"*40)
    
    # Thai patterns
    total_patterns = [
        r'ยอดรวม.*?([\d,]+\.?\d*)',
        r'จำนวนเงินรวม.*?([\d,]+\.?\d*)',
        r'รวม.*?([\d,]+\.?\d*)',
        # English patterns
        r'Total.*?([\d,]+\.?\d*)',
        r'Amount due.*?([\d,]+\.?\d*)',
        r'Grand total.*?([\d,]+\.?\d*)'
    ]
    
    for pattern in total_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE | re.MULTILINE)
        if matches:
            print(f"Pattern '{pattern}' found:")
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    print(f"  - {match} = {amount:,.2f}")
                except:
                    pass
    
    # Look for all amounts in the invoice
    print("\n\nAll amounts found:")
    print("-"*40)
    amount_pattern = re.compile(r'([\d,]+\.\d{2})')
    amounts = []
    for match in amount_pattern.findall(full_text):
        try:
            amount = float(match.replace(',', ''))
            amounts.append(amount)
            print(f"  {match} = {amount:,.2f}")
        except:
            pass
    
    # Try to identify line items vs totals
    print("\n\nPotential line items (amounts between 10 and 100,000):")
    print("-"*40)
    line_items = [a for a in amounts if 10 <= abs(a) <= 100000]
    for item in line_items:
        print(f"  {item:,.2f}")
    print(f"\nSum of potential line items: {sum(line_items):,.2f}")

if __name__ == "__main__":
    # Check the specific invoice mentioned by user
    check_invoice("../Invoice for testing/5297692778.pdf")