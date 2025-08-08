#!/usr/bin/env python3
"""Check for misclassified files"""

import json

with open('all_138_files_updated_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

misclassified = []
for filename, data in report['files'].items():
    platform = data['platform']
    
    # Check classification
    if filename.startswith('24') and platform != 'Facebook':
        misclassified.append(f'{filename}: classified as {platform}, should be Facebook')
    elif filename.startswith('5') and platform != 'Google':
        misclassified.append(f'{filename}: classified as {platform}, should be Google')
    elif filename.startswith('THTT') and platform != 'TikTok':
        misclassified.append(f'{filename}: classified as {platform}, should be TikTok')

if misclassified:
    print('Misclassified files:')
    for item in misclassified:
        print(f'  {item}')
else:
    print('All files correctly classified')

# Count by prefix
fb_count = sum(1 for f in report['files'] if f.startswith('24'))
google_count = sum(1 for f in report['files'] if f.startswith('5'))
tiktok_count = sum(1 for f in report['files'] if f.startswith('THTT'))

print(f'\nActual counts by filename prefix:')
print(f'  Facebook (24*): {fb_count}')
print(f'  Google (5*): {google_count}')
print(f'  TikTok (THTT*): {tiktok_count}')
print(f'  Total: {fb_count + google_count + tiktok_count}')

# Show platform classification counts
print(f'\nReport shows:')
print(f'  Facebook: {report["summary"]["by_platform"]["Facebook"]["files"]}')
print(f'  Google: {report["summary"]["by_platform"]["Google"]["files"]}')
print(f'  TikTok: {report["summary"]["by_platform"]["TikTok"]["files"]}')