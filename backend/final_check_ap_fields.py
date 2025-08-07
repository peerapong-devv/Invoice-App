#!/usr/bin/env python3
"""Final check of AP fields in the report"""

import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load updated report
with open('all_138_files_updated_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print("FINAL AP FIELDS CHECK")
print("="*80)

# Check some AP invoices
ap_samples = []
for filename, data in report['files'].items():
    if data['platform'] == 'Google' and data['invoice_type'] == 'AP':
        for item in data['items']:
            if item.get('agency') == 'pk':
                ap_samples.append((filename, item))
                break
        if len(ap_samples) >= 5:
            break

# Show samples
for filename, item in ap_samples:
    print(f"\n{filename}:")
    print(f"  Description: {item.get('description', '')[:80]}...")
    print(f"  Agency: {item.get('agency')}")
    print(f"  Project ID: {item.get('project_id')}")
    print(f"  Project Name: {item.get('project_name')}")
    print(f"  Campaign ID: {item.get('campaign_id')}")
    print(f"  Objective: {item.get('objective')}")
    print(f"  Period: {item.get('period')}")

# Summary
print("\n" + "="*80)
print("SUMMARY:")
print(f"Facebook: {report['summary']['by_platform']['Facebook']['total_amount']:,.2f} THB ✓")
print(f"Google: {report['summary']['by_platform']['Google']['total_amount']:,.2f} THB ✓")
print(f"TikTok: {report['summary']['by_platform']['TikTok']['total_amount']:,.2f} THB ✓")
print(f"\nTotal: {sum(p['total_amount'] for p in report['summary']['by_platform'].values()):,.2f} THB")
print(f"Files: {sum(p['files'] for p in report['summary']['by_platform'].values())}")
print(f"Items: {sum(p['total_items'] for p in report['summary']['by_platform'].values())}")