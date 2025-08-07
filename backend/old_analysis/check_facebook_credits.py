#!/usr/bin/env python3
"""Check for Facebook credit memos or negative amounts"""

import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the analysis
with open('facebook_totals_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("FACEBOOK CREDIT MEMOS AND NEGATIVE AMOUNTS")
print("="*80)

# Check for files with negative totals
negative_files = []
for file_data in data['files']:
    if file_data['total'] < 0:
        negative_files.append(file_data)

print(f"Files with negative totals: {len(negative_files)}")

# Check for items with negative amounts
negative_items = []
for file_data in data['files']:
    for item in file_data['items']:
        if item['amount'] < 0:
            negative_items.append({
                'file': file_data['filename'],
                'amount': item['amount'],
                'description': item['description']
            })

print(f"Items with negative amounts: {len(negative_items)}")

if negative_items:
    print("\nNegative items found:")
    for item in negative_items:
        print(f"  {item['file']}: {item['amount']:,.2f} - {item['description'][:50]}...")

# Check for credit-related keywords
credit_keywords = ['credit', 'adjustment', 'refund', 'reversal', 'correction']
credit_items = []

for file_data in data['files']:
    for item in file_data['items']:
        desc_lower = item.get('description', '').lower()
        if any(keyword in desc_lower for keyword in credit_keywords):
            credit_items.append({
                'file': file_data['filename'],
                'amount': item['amount'],
                'description': item['description']
            })

print(f"\nItems with credit-related keywords: {len(credit_items)}")
if credit_items:
    for item in credit_items:
        print(f"  {item['file']}: {item['amount']:,.2f} - {item['description'][:50]}...")

# Check if expected total includes or excludes certain files
print("\n" + "="*80)
print("HYPOTHESIS: File 246952155.pdf might be excluded from expected total")
print("="*80)

# Calculate total without this file
total_without_246952155 = sum(f['total'] for f in data['files'] if f['filename'] != '246952155.pdf')
print(f"Total without 246952155.pdf: {total_without_246952155:,.2f}")
print(f"Expected total: {data['expected_total']:,.2f}")
print(f"Difference: {total_without_246952155 - data['expected_total']:,.2f}")

# Also try with the file that has 2,645.23 exactly
print("\nChecking if any file has exactly 2,645.23:")
for file_data in data['files']:
    if abs(file_data['total'] - 2645.23) < 0.01:
        print(f"  {file_data['filename']}: {file_data['total']:,.2f}")