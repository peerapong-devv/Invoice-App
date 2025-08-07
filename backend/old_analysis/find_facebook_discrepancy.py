#!/usr/bin/env python3
"""Find specific Facebook invoice causing discrepancy"""

import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the analysis
with open('facebook_totals_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Look for the exact difference amount
DIFFERENCE = 2645.23

print("="*80)
print("SEARCHING FOR FACEBOOK DISCREPANCY")
print("="*80)
print(f"Looking for amount: {DIFFERENCE:,.2f}")

# Check each invoice's items
found = False
for file_data in data['files']:
    for item in file_data['items']:
        if abs(item['amount'] - DIFFERENCE) < 0.01:
            print(f"\nFOUND EXACT MATCH!")
            print(f"File: {file_data['filename']}")
            print(f"Item: {item['line_number']}")
            print(f"Amount: {item['amount']:,.2f}")
            print(f"Description: {item['description']}")
            print(f"Type: {item['invoice_type']}")
            found = True

# Check if any file total equals the difference
for file_data in data['files']:
    if abs(file_data['total'] - DIFFERENCE) < 0.01:
        print(f"\nFile total matches difference!")
        print(f"File: {file_data['filename']}")
        print(f"Total: {file_data['total']:,.2f}")
        print(f"Items: {file_data['items_count']}")
        found = True

# Check for files with suspicious totals
print("\n" + "="*80)
print("FILES WITH SINGLE ITEMS (potential parsing issues):")
print("="*80)

single_item_files = [f for f in data['files'] if f['items_count'] == 1]
for f in single_item_files:
    print(f"{f['filename']}: {f['total']:,.2f} - {f['items'][0]['description'][:60]}...")

# Check a specific file that might have the issue
print("\n" + "="*80)
print("CHECKING FILE WITH EXACT DIFFERENCE AMOUNT")
print("="*80)

# File 246952155.pdf has total 2,649.51 which is very close to 2,645.23
target_file = next((f for f in data['files'] if f['filename'] == '246952155.pdf'), None)
if target_file:
    print(f"File: {target_file['filename']}")
    print(f"Total: {target_file['total']:,.2f}")
    print(f"Expected difference: {DIFFERENCE:,.2f}")
    print(f"Actual difference: {target_file['total'] - DIFFERENCE:.2f}")
    print(f"\nItems in this file:")
    for item in target_file['items']:
        print(f"  Line {item['line_number']}: {item['amount']:,.2f} - {item['description'][:50]}...")

if not found:
    print("\nNo exact match found for the difference amount.")
    print("The discrepancy might be due to:")
    print("1. Multiple small rounding errors across files")
    print("2. A parsing issue in one of the files")
    print("3. An item that should be excluded but is included")