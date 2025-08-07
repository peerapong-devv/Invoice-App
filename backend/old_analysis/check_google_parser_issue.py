#!/usr/bin/env python3
"""Check why Google parser extracts so few items"""

import json
import fitz
import os

# Load report to see which files have issues
with open('all_138_files_detailed_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Find a Google AP invoice with only 1 item
google_ap_files = []
for filename, data in report['files'].items():
    if data.get('platform') == 'Google' and data.get('invoice_type') == 'AP' and data.get('total_items') == 1:
        google_ap_files.append(filename)

print(f"Found {len(google_ap_files)} Google AP files with only 1 item")
print("\nChecking first file:", google_ap_files[0])

# Read the actual PDF
invoice_path = os.path.join('..', 'Invoice for testing', google_ap_files[0])
with fitz.open(invoice_path) as doc:
    text = doc[0].get_text()
    
    # Count potential line items
    lines = text.split('\n')
    
    # Look for patterns that indicate line items
    pk_patterns = []
    amounts = []
    
    for line in lines:
        # Look for pk| patterns
        if 'pk|' in line or 'p\u200bk\u200b|' in line:
            pk_patterns.append(line.strip())
        
        # Look for amounts (numbers with decimals)
        if any(char.isdigit() for char in line):
            # Check if it looks like an amount
            line_clean = line.strip()
            if '.' in line_clean and any(c.isdigit() for c in line_clean):
                try:
                    # Try to extract number
                    import re
                    numbers = re.findall(r'[\d,]+\.\d{2}', line_clean)
                    for num in numbers:
                        amount = float(num.replace(',', ''))
                        if 10 <= amount <= 1000000:  # Reasonable amount range
                            amounts.append((line_clean, amount))
                except:
                    pass

print(f"\nFound {len(pk_patterns)} lines with pk| patterns")
print(f"Found {len(amounts)} potential amount lines")

if pk_patterns:
    print("\nFirst 5 pk| patterns found:")
    for i, pattern in enumerate(pk_patterns[:5]):
        print(f"  {i+1}. {pattern[:80]}...")

if amounts:
    print(f"\nFirst 10 amounts found:")
    for i, (line, amount) in enumerate(amounts[:10]):
        print(f"  {i+1}. {amount:,.2f} - {line[:60]}...")

# Check what the parser extracted
print(f"\n\nWhat the parser extracted:")
file_data = report['files'][google_ap_files[0]]
print(f"Items: {file_data.get('total_items')}")
print(f"Total: {file_data.get('total_amount'):,.2f}")
if 'items' in file_data:
    for item in file_data['items']:
        print(f"  - {item.get('description', 'N/A')}: {item.get('amount', 0):,.2f}")

print("\n\nCONCLUSION: Google parser is using hardcoded patterns for only 3 files")
print("and falling back to single total for all other files!")
print("This explains why average is 1.09 items/file instead of extracting all line items.")