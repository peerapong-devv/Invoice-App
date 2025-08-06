#!/usr/bin/env python3
"""Extract amounts from Google invoice"""

import fitz
import re

def extract_amounts(filepath):
    """Extract all monetary amounts from invoice"""
    with fitz.open(filepath) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text()
    
    # Clean text
    full_text = full_text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    
    # Find all amounts (with Thai baht symbol or without)
    amount_patterns = [
        r'฿([\d,]+\.?\d*)',  # Thai baht symbol
        r'THB\s*([\d,]+\.?\d*)',  # THB prefix
        r'([\d,]+\.\d{2})(?:\s|$)',  # Standard decimal amounts
        r'(-[\d,]+\.\d{2})(?:\s|$)',  # Negative amounts
    ]
    
    all_amounts = []
    for pattern in amount_patterns:
        matches = re.findall(pattern, full_text)
        for match in matches:
            try:
                # Remove commas and convert to float
                amount_str = match.replace(',', '').replace('฿', '').strip()
                amount = float(amount_str)
                all_amounts.append(amount)
            except:
                pass
    
    # Remove duplicates and sort
    unique_amounts = sorted(list(set(all_amounts)), reverse=True)
    
    return unique_amounts

# Check the three invoices
invoices = ['5297692778', '5297692787', '5297692790']

for inv_num in invoices:
    filepath = f"../Invoice for testing/{inv_num}.pdf"
    amounts = extract_amounts(filepath)
    
    print(f"\nInvoice {inv_num}:")
    print("-" * 40)
    
    # Show larger amounts (likely totals or subtotals)
    large_amounts = [a for a in amounts if abs(a) >= 1000]
    print("Large amounts (>= 1000):")
    for a in large_amounts:
        print(f"  {a:,.2f}")
    
    # Show medium amounts (likely line items)
    medium_amounts = [a for a in amounts if 10 <= abs(a) < 1000]
    print("\nMedium amounts (10-999):")
    for a in medium_amounts:
        print(f"  {a:,.2f}")
    
    # Look for the most likely total (usually appears multiple times)
    from collections import Counter
    amount_counts = Counter(amounts)
    most_common = amount_counts.most_common(5)
    print("\nMost frequent amounts:")
    for amount, count in most_common:
        if abs(amount) > 10:  # Ignore small amounts
            print(f"  {amount:,.2f} (appears {count} times)")