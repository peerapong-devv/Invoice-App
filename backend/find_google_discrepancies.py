#!/usr/bin/env python3
"""Find which Google files have the biggest discrepancies"""

import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the report
with open('all_138_files_updated_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Expected totals per file (would need actual data, using estimates)
print("GOOGLE FILES ANALYSIS")
print("="*80)

# Get all Google files
google_files = [(f, data) for f, data in report['files'].items() if data['platform'] == 'Google']
google_files.sort(key=lambda x: abs(x[1]['total_amount']), reverse=True)

print(f"Total Google files: {len(google_files)}")
print(f"\nTop 20 files by amount:")
print(f"{'Filename':<25} {'Type':<8} {'Items':<6} {'Amount':>12}")
print("-"*60)

for filename, data in google_files[:20]:
    print(f"{filename:<25} {data['invoice_type']:<8} {data['total_items']:<6} {data['total_amount']:>12,.2f}")

# Files with only 1 item
single_item_files = [(f, data) for f, data in google_files if data['total_items'] == 1]
print(f"\n\nFiles with only 1 item: {len(single_item_files)}")
print(f"Total amount from single-item files: {sum(d['total_amount'] for f, d in single_item_files):,.2f}")

# Files with 0 items
zero_item_files = [(f, data) for f, data in google_files if data['total_items'] == 0]
print(f"\nFiles with 0 items: {len(zero_item_files)}")
for f, d in zero_item_files:
    print(f"  {f}")

# Check specific problem files
problem_files = ['5297692778.pdf', '5297692790.pdf', '5297785878.pdf', '5297735036.pdf']
print(f"\n\nPROBLEM FILES DETAILS:")
print("-"*80)

for pf in problem_files:
    if pf in report['files']:
        data = report['files'][pf]
        print(f"\n{pf}:")
        print(f"  Type: {data['invoice_type']}")
        print(f"  Total: {data['total_amount']:,.2f}")
        print(f"  Items: {data['total_items']}")
        
        # Show items
        for item in data['items'][:5]:
            print(f"    {item['line_number']}. {item['amount']:>10,.2f} - {item.get('description', '')[:50]}...")
            if item.get('agency'):
                print(f"       Agency: {item['agency']}, Project: {item.get('project_id')}")