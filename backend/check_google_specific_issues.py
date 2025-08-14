#!/usr/bin/env python3
"""Check specific Google issues mentioned by user"""

import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

# Load the updated report
with open('all_138_files_updated_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Specific issues to check
issues = {
    '5297692778.pdf': 'Should have AP fields extracted',
    '5297692790.pdf': 'Should be -6,284.42 (negative)',
    '5297785878.pdf': 'Should have only 1 line with -1.66',
    '5297735036.pdf': 'Non-AP but all descriptions should be different'
}

print("CHECKING SPECIFIC GOOGLE ISSUES")
print("="*80)

for filename, issue in issues.items():
    print(f"\n{filename}: {issue}")
    
    if filename in report['files']:
        file_data = report['files'][filename]
        print(f"  Invoice type: {file_data['invoice_type']}")
        print(f"  Total items: {file_data['total_items']}")
        print(f"  Total amount: {file_data['total_amount']:,.2f}")
        
        # Check AP fields
        ap_items = [item for item in file_data['items'] if item.get('agency') == 'pk']
        print(f"  Items with AP fields: {len(ap_items)}")
        
        # Show items
        print("  Items:")
        for item in file_data['items'][:5]:  # Show first 5
            desc = item.get('description', '')[:60]
            print(f"    {item['line_number']}. {item['amount']:,.2f} - {desc}...")
            if item.get('agency'):
                print(f"       Agency: {item['agency']}, Project: {item.get('project_id')}")
    else:
        print(f"  NOT FOUND IN REPORT!")

# Check overall Google accuracy
print("\n" + "="*80)
print("GOOGLE PARSER ACCURACY")
print("="*80)

google_files = [f for f, data in report['files'].items() if data['platform'] == 'Google']
total_google = sum(data['total_amount'] for data in report['files'].values() if data['platform'] == 'Google')
expected_google = 2362684.79

print(f"Total Google files: {len(google_files)}")
print(f"Total amount: {total_google:,.2f}")
print(f"Expected: {expected_google:,.2f}")
print(f"Difference: {abs(total_google - expected_google):,.2f}")
print(f"Accuracy: {(1 - abs(total_google - expected_google) / expected_google) * 100:.2f}%")

# Check which files have the biggest discrepancies
print("\nFiles with potential issues:")
problem_files = []
for filename in google_files:
    file_data = report['files'][filename]
    if file_data['total_items'] == 0:
        problem_files.append((filename, 'No items extracted', file_data['total_amount']))
    elif file_data['total_items'] == 1 and file_data['invoice_type'] != 'Unknown':
        problem_files.append((filename, 'Only 1 item extracted', file_data['total_amount']))

problem_files.sort(key=lambda x: abs(x[2]), reverse=True)
for filename, issue, amount in problem_files[:10]:
    print(f"  {filename}: {issue} (amount: {amount:,.2f})")