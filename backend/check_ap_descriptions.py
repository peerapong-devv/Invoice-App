#!/usr/bin/env python3
"""Check AP invoice descriptions to understand the pattern"""

import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load report
with open('all_138_files_updated_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Find AP invoices
ap_invoices = []
for filename, data in report['files'].items():
    if data['platform'] == 'Google' and data['invoice_type'] == 'AP':
        ap_invoices.append((filename, data))

print("AP INVOICE DESCRIPTIONS ANALYSIS")
print("="*80)
print(f"Total AP invoices: {len(ap_invoices)}")

# Show sample descriptions
print("\nSample AP descriptions:")
count = 0
for filename, data in ap_invoices[:5]:
    print(f"\n{filename}:")
    for item in data['items'][:3]:
        desc = item.get('description', '')
        print(f"  Description: {desc}")
        print(f"  Agency: {item.get('agency')}")
        print(f"  Project ID: {item.get('project_id')}")
        print(f"  Project Name: {item.get('project_name')}")
        print(f"  Campaign ID: {item.get('campaign_id')}")
        print(f"  Objective: {item.get('objective')}")
        print()
        
        # Check if description has fragmented pk| pattern
        if 'p k |' in desc or 'p\nk\n|' in desc:
            print("  >> Has fragmented pk| pattern with spaces!")
            # Show how it should be parsed
            clean_desc = desc.replace(' ', '').replace('\n', '')
            print(f"  >> Cleaned: {clean_desc[:100]}...")
            
# Look for patterns
print("\n" + "="*80)
print("PATTERN ANALYSIS:")

# Check a specific description
sample_desc = "(฿) p k | 4 0 1 0 9 | S D H _ p k _ t h - s i n g l e - d e t a c h e d - h o u s e - c e n t r o - r"
print(f"\nSample description: {sample_desc}")

# Remove spaces
clean = sample_desc.replace(' ', '')
print(f"Cleaned: {clean}")

# Extract pattern
import re

# Extract pk| pattern
if 'pk|' in clean:
    # Extract project ID
    id_match = re.search(r'pk\|(\d{5,6})', clean)
    if id_match:
        print(f"Project ID: {id_match.group(1)}")
    
    # Extract project name/campaign
    if 'SDH_pk_' in clean:
        project_match = re.search(r'(SDH_pk_[a-z\-]+)', clean)
        if project_match:
            print(f"Project/Campaign: {project_match.group(1)}")