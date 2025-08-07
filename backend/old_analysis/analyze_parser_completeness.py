#!/usr/bin/env python3
"""Analyze parser completeness - check if all line items are extracted"""

import json

# Load the report
with open('all_138_files_detailed_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print("="*80)
print("PARSER COMPLETENESS ANALYSIS")
print("="*80)

# Analyze by platform
platforms = {}
for filename, file_data in report['files'].items():
    platform = file_data.get('platform', 'Unknown')
    if platform not in platforms:
        platforms[platform] = {
            'files': 0,
            'total_items': 0,
            'files_with_1_item': [],
            'files_with_multiple_items': [],
            'item_distribution': {}
        }
    
    platforms[platform]['files'] += 1
    items_count = file_data.get('total_items', 0)
    platforms[platform]['total_items'] += items_count
    
    # Track item distribution
    if items_count not in platforms[platform]['item_distribution']:
        platforms[platform]['item_distribution'][items_count] = 0
    platforms[platform]['item_distribution'][items_count] += 1
    
    # Track files with only 1 item (potentially incomplete)
    if items_count == 1:
        platforms[platform]['files_with_1_item'].append(filename)
    else:
        platforms[platform]['files_with_multiple_items'].append(filename)

# Print analysis
for platform, data in platforms.items():
    print(f"\n{platform} Platform Analysis:")
    print("-"*50)
    print(f"Total files: {data['files']}")
    print(f"Total items extracted: {data['total_items']}")
    print(f"Average items per file: {data['total_items']/data['files']:.2f}")
    print(f"Files with only 1 item: {len(data['files_with_1_item'])}")
    print(f"Files with multiple items: {len(data['files_with_multiple_items'])}")
    
    print(f"\nItem count distribution:")
    for item_count in sorted(data['item_distribution'].keys()):
        file_count = data['item_distribution'][item_count]
        print(f"  {item_count} items: {file_count} files")
    
    # Show files with only 1 item (potential problems)
    if data['files_with_1_item'] and platform == 'Google':
        print(f"\nGoogle files with only 1 item (potentially incomplete):")
        for f in data['files_with_1_item'][:10]:  # Show first 10
            print(f"  - {f}")
        if len(data['files_with_1_item']) > 10:
            print(f"  ... and {len(data['files_with_1_item']) - 10} more")

# Check specific Google files
print("\n" + "="*80)
print("GOOGLE FILES DETAILED CHECK")
print("="*80)

google_issues = []
for filename, file_data in report['files'].items():
    if file_data.get('platform') == 'Google':
        items = file_data.get('items', [])
        total_items = file_data.get('total_items', 0)
        
        # Check for potential issues
        has_fees = any('ค่าธรรมเนียม' in str(item.get('description', '')) for item in items)
        has_campaign = any('pk|' in str(item.get('description', '')) or 
                          'Campaign' in str(item.get('description', '')) for item in items)
        
        if total_items == 1 and not has_fees:
            google_issues.append({
                'file': filename,
                'items': total_items,
                'type': file_data.get('invoice_type', 'Unknown'),
                'amount': file_data.get('total_amount', 0)
            })

print(f"Google files with potential missing line items: {len(google_issues)}")
print("\nFirst 10 problematic Google files:")
for issue in google_issues[:10]:
    print(f"  {issue['file']}: {issue['items']} items, Type: {issue['type']}, Amount: {issue['amount']:,.2f}")

# Compare average items per file
print("\n" + "="*80)
print("COMPARISON SUMMARY")
print("="*80)
print(f"TikTok: {platforms.get('TikTok', {}).get('total_items', 0)/platforms.get('TikTok', {}).get('files', 1):.2f} items/file")
print(f"Facebook: {platforms.get('Facebook', {}).get('total_items', 0)/platforms.get('Facebook', {}).get('files', 1):.2f} items/file")
print(f"Google: {platforms.get('Google', {}).get('total_items', 0)/platforms.get('Google', {}).get('files', 1):.2f} items/file")

print("\nCONCLUSION:")
print("- TikTok parser extracts detailed line items (average ~7.9 items/file)")
print("- Facebook parser extracts detailed line items (average ~23.4 items/file)")
print("- Google parser extracts very few items (average ~1.1 items/file) - NEEDS FIX!")