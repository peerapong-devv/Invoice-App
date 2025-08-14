#!/usr/bin/env python3
"""Analyze full descriptions to understand the pattern"""

import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# Load report
with open('all_138_files_updated_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print("ANALYZING FULL AP DESCRIPTIONS")
print("="*80)

# Get some AP invoices
ap_samples = []
for filename, data in report['files'].items():
    if data['platform'] == 'Google' and data['invoice_type'] == 'AP':
        for item in data['items']:
            if item.get('agency') == 'pk':
                ap_samples.append((filename, item))
                break
        if len(ap_samples) >= 5:
            break

# Analyze patterns
for filename, item in ap_samples:
    print(f"\n{filename}:")
    desc = item.get('description', '')
    print(f"Raw description: {desc}")
    
    # Clean it
    clean = desc.replace(' ', '').replace('\n', '')
    print(f"Cleaned: {clean}")
    
    # Parse the pattern
    # Expected: pk|{id}|{project}_none_{objective}_{type}_{campaign}_{details}
    
    # Try to extract all parts
    pk_match = re.search(r'pk\|(\d+)\|([^|]+)', clean)
    if pk_match:
        project_id = pk_match.group(1)
        rest = pk_match.group(2)
        
        print(f"\nExtracted:")
        print(f"  Project ID: {project_id}")
        
        # Split by underscore to get parts
        parts = rest.split('_')
        print(f"  Parts: {parts}")
        
        # Find patterns
        if 'none' in parts:
            none_idx = parts.index('none')
            # Before 'none' is project name
            project_name = '_'.join(parts[:none_idx])
            print(f"  Project name: {project_name}")
            
            # After 'none' should be objective, type, campaign
            if none_idx + 1 < len(parts):
                print(f"  Objective: {parts[none_idx + 1]}")
            if none_idx + 2 < len(parts):
                print(f"  Type: {parts[none_idx + 2]}")
            if none_idx + 3 < len(parts):
                print(f"  Campaign part: {parts[none_idx + 3]}")
    
    # Look for campaign ID patterns in full text
    campaign_patterns = [
        r'\b(\d{4}P\d+)\b',  # 2089P12
        r'(GDNQ[A-Z0-9]+)',  # GDNQ2Y25
        r'\[ST\]\|(\d+)',    # [ST]|2100P02
    ]
    
    print("\n  Looking for campaign IDs:")
    for pattern in campaign_patterns:
        match = re.search(pattern, clean)
        if match:
            print(f"    Found: {match.group(1) if '|' not in pattern else match.group(0)}")
    
    # Check what we currently have
    print(f"\n  Current extraction:")
    print(f"    Objective: {item.get('objective')}")
    print(f"    Campaign ID: {item.get('campaign_id')}")
    print(f"    Period: {item.get('period')}")
    
    print("-"*80)