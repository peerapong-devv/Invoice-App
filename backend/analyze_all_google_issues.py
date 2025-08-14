#!/usr/bin/env python3
"""Analyze ALL Google invoice issues comprehensively"""

import os
import sys
import json
import fitz
import re

sys.stdout.reconfigure(encoding='utf-8')

# Load current report to see all issues
with open('all_138_files_updated_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

invoice_dir = os.path.join('..', 'Invoice for testing')

# Expected totals from user
expected_total = 2362684.79
actual_total = report['summary']['by_platform']['Google']['total_amount']
difference = expected_total - actual_total

print("COMPREHENSIVE GOOGLE INVOICE ANALYSIS")
print("="*80)
print(f"Expected total: {expected_total:,.2f} THB")
print(f"Actual total: {actual_total:,.2f} THB")
print(f"Difference: {difference:,.2f} THB")
print(f"Accuracy: {(actual_total/expected_total)*100:.2f}%")
print()

# Analyze each Google file
google_files = [(f, data) for f, data in report['files'].items() if data['platform'] == 'Google']
print(f"Total Google files: {len(google_files)}")

# Categories of issues
issues = {
    'single_item_large_amount': [],
    'wrong_invoice_type': [],
    'duplicate_descriptions': [],
    'missing_ap_fields': [],
    'wrong_total': [],
    'too_few_items': []
}

print("\nANALYZING EACH FILE:")
print("-"*80)

for filename, data in google_files:
    filepath = os.path.join(invoice_dir, filename)
    
    # Check for issues
    problems = []
    
    # Issue 1: Single item for large amounts
    if data['total_items'] == 1 and abs(data['total_amount']) > 10000:
        issues['single_item_large_amount'].append((filename, data['total_amount']))
        problems.append("Single item for large amount")
    
    # Issue 2: Check invoice type
    with fitz.open(filepath) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # Clean text
        clean_text = full_text.replace('\u200b', '')
        
        # Check for AP indicators
        has_ap_pattern = False
        if 'pk|' in clean_text or 'pk |' in clean_text:
            has_ap_pattern = True
        elif 'pk' in clean_text and '|' in clean_text:
            # Check fragmented
            no_spaces = clean_text.replace('\n', '').replace(' ', '')
            if 'pk|' in no_spaces:
                has_ap_pattern = True
        
        # Check for campaign IDs
        if re.search(r'2089P\d+|2159P\d+|2218P\d+', clean_text):
            has_ap_pattern = True
        
        if has_ap_pattern and data['invoice_type'] != 'AP':
            issues['wrong_invoice_type'].append((filename, 'Should be AP'))
            problems.append("Wrong type: should be AP")
        
        # Issue 3: Check for pk| fields in AP invoices
        if data['invoice_type'] == 'AP' or has_ap_pattern:
            ap_items = [item for item in data['items'] if item.get('agency') == 'pk']
            if not ap_items:
                issues['missing_ap_fields'].append(filename)
                problems.append("Missing AP fields")
    
    # Issue 4: Duplicate descriptions
    if data['total_items'] > 1:
        descriptions = [item.get('description', '') for item in data['items']]
        unique_descs = set(descriptions)
        if len(unique_descs) == 1:
            issues['duplicate_descriptions'].append(filename)
            problems.append("All items have same description")
    
    # Issue 5: Check specific files with known issues
    known_issues = {
        '5297692790.pdf': -6284.42,
        '5297785878.pdf': -1.66,
        '5297692778.pdf': 18550.72
    }
    
    if filename in known_issues:
        expected = known_issues[filename]
        if abs(data['total_amount'] - expected) > 0.01:
            issues['wrong_total'].append((filename, data['total_amount'], expected))
            problems.append(f"Wrong total: {data['total_amount']:.2f} vs {expected:.2f}")
    
    if problems:
        print(f"\n{filename}:")
        print(f"  Current: {data['total_items']} items, {data['total_amount']:,.2f} THB, Type: {data['invoice_type']}")
        print(f"  Issues: {', '.join(problems)}")

# Summary of issues
print("\n" + "="*80)
print("SUMMARY OF ISSUES:")
print("="*80)

print(f"\n1. Single item for large amounts: {len(issues['single_item_large_amount'])} files")
for f, amount in issues['single_item_large_amount'][:5]:
    print(f"   {f}: {amount:,.2f} THB")

print(f"\n2. Wrong invoice type: {len(issues['wrong_invoice_type'])} files")
for f, issue in issues['wrong_invoice_type'][:5]:
    print(f"   {f}: {issue}")

print(f"\n3. Missing AP fields: {len(issues['missing_ap_fields'])} files")
for f in issues['missing_ap_fields'][:5]:
    print(f"   {f}")

print(f"\n4. Duplicate descriptions: {len(issues['duplicate_descriptions'])} files")
for f in issues['duplicate_descriptions'][:5]:
    print(f"   {f}")

print(f"\n5. Wrong totals: {len(issues['wrong_total'])} files")
for f, actual, expected in issues['wrong_total']:
    print(f"   {f}: {actual:.2f} vs {expected:.2f} (diff: {actual-expected:.2f})")

# Check a specific problematic file in detail
print("\n" + "="*80)
print("DETAILED CHECK: 5298156820.pdf (largest amount)")
print("="*80)

filepath = os.path.join(invoice_dir, '5298156820.pdf')
with fitz.open(filepath) as doc:
    print(f"Pages: {len(doc)}")
    
    if len(doc) >= 2:
        page2 = doc[1]
        blocks = page2.get_text("blocks")
        
        print(f"\nPage 2 has {len(blocks)} blocks")
        print("\nLooking for line items:")
        
        # Find amounts
        for i, block in enumerate(blocks):
            if len(block) >= 5:
                text = block[4].strip()
                if re.search(r'\d{1,3}(?:,\d{3})*\.\d{2}', text) and i < 30:
                    print(f"  Block {i}: {text[:80]}")