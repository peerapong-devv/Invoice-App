#!/usr/bin/env python3
"""Check if AP fields are properly extracted in the updated report"""

import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load updated report
with open('all_138_files_updated_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Check AP invoices
print("AP INVOICE FIELDS CHECK")
print("="*80)

ap_count = 0
fields_complete = 0
fields_missing = 0

for filename, data in report['files'].items():
    if data['platform'] == 'Google' and data['invoice_type'] == 'AP':
        ap_count += 1
        
        # Check first item with pk|
        for item in data['items']:
            if item.get('agency') == 'pk':
                has_all_fields = all([
                    item.get('project_id'),
                    item.get('project_name'),
                    item.get('campaign_id') or item.get('objective')  # At least one
                ])
                
                if has_all_fields:
                    fields_complete += 1
                else:
                    fields_missing += 1
                
                # Show sample
                if ap_count <= 5:
                    print(f"\n{filename}:")
                    print(f"  Agency: {item.get('agency')}")
                    print(f"  Project ID: {item.get('project_id')}")
                    print(f"  Project Name: {item.get('project_name')}")
                    print(f"  Campaign ID: {item.get('campaign_id')}")
                    print(f"  Objective: {item.get('objective')}")
                    print(f"  Description: {item.get('description', '')[:60]}...")
                
                break  # Check only first pk| item

print(f"\n\nSUMMARY:")
print(f"Total AP invoices: {ap_count}")
print(f"With complete fields: {fields_complete}")
print(f"With missing fields: {fields_missing}")

# Check total accuracy
print(f"\n\nPLATFORM TOTALS:")
for platform, data in report['summary']['by_platform'].items():
    print(f"{platform}: {data['total_amount']:,.2f} THB ({data['files']} files)")

print(f"\nExpected Google total: 2,362,684.79 THB")
google_total = report['summary']['by_platform']['Google']['total_amount']
print(f"Actual Google total: {google_total:,.2f} THB")
print(f"Accuracy: {(google_total/2362684.79)*100:.2f}%")