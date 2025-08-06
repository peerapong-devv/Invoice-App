#!/usr/bin/env python3
"""Test single Google file"""

import sys
import fitz
sys.stdout.reconfigure(encoding='utf-8')

from google_parser_final_100 import parse_google_invoice

filename = '5300624442.pdf'
filepath = f'../Invoice for testing/{filename}'

with fitz.open(filepath) as doc:
    text = ''
    for page in doc:
        text += page.get_text()

print(f"File: {filename}")
print("="*60)

# Show first 30 lines
lines = text.split('\n')
for i, line in enumerate(lines[:30]):
    if line.strip():
        print(f"{i:3d}: {line}")

print("\n" + "="*60)
print("Looking for table area...")

# Look for table
for i, line in enumerate(lines):
    if 'คำอธิบาย' in line or 'Description' in line:
        print(f"Found header at line {i}: {line}")
        # Show next 10 lines
        for j in range(i, min(i+10, len(lines))):
            print(f"{j:3d}: {lines[j]}")
        break

# Parse
print("\n" + "="*60)
print("Parsing...")
items = parse_google_invoice(text, filename)
print(f"Found {len(items)} items")

if items:
    for item in items:
        print(f"  Line {item['line_number']}: {item['description'][:60]}... = {item['amount']:,.2f}")