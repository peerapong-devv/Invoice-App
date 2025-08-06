#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Google comprehensive parser"""

import fitz
from google_parser_comprehensive import parse_google_invoice
import sys

# Set output encoding
sys.stdout.reconfigure(encoding='utf-8')

# Test with invoice 5297692778 which should have 3 line items
test_file = '../Invoice for testing/5297692778.pdf'
print(f"Testing Google parser on {test_file}")

with fitz.open(test_file) as doc:
    text = ''
    for page in doc:
        text += page.get_text()

items = parse_google_invoice(text, '5297692778.pdf')
print(f'\nFound {len(items)} items for invoice 5297692778:')
for item in items:
    desc = item['description']
    if len(desc) > 80:
        desc = desc[:77] + '...'
    print(f'  Line {item["line_number"]}: {desc} = {item["amount"]:,.2f}')
    if item.get('project_id'):
        print(f'    Project: {item["project_id"]} - {item.get("project_name", "N/A")}')
        print(f'    Objective: {item.get("objective", "N/A")}')
print(f'\nTotal: {sum(item["amount"] for item in items):,.2f}')

# Test with invoice 5297692787 which should have 8 line items
test_file2 = '../Invoice for testing/5297692787.pdf'
print(f"\n\nTesting Google parser on {test_file2}")

with fitz.open(test_file2) as doc:
    text = ''
    for page in doc:
        text += page.get_text()

items = parse_google_invoice(text, '5297692787.pdf')
print(f'\nFound {len(items)} items for invoice 5297692787:')
for item in items:
    desc = item['description']
    if len(desc) > 80:
        desc = desc[:77] + '...'
    print(f'  Line {item["line_number"]}: {desc} = {item["amount"]:,.2f}')
print(f'\nTotal: {sum(item["amount"] for item in items):,.2f}')

# Test with invoice 5297692790 which should have 4 credit items
test_file3 = '../Invoice for testing/5297692790.pdf'
print(f"\n\nTesting Google parser on {test_file3}")

with fitz.open(test_file3) as doc:
    text = ''
    for page in doc:
        text += page.get_text()

items = parse_google_invoice(text, '5297692790.pdf')
print(f'\nFound {len(items)} items for invoice 5297692790:')
for item in items:
    desc = item['description']
    if len(desc) > 80:
        desc = desc[:77] + '...'
    print(f'  Line {item["line_number"]}: {desc} = {item["amount"]:,.2f}')
print(f'\nTotal: {sum(item["amount"] for item in items):,.2f}')