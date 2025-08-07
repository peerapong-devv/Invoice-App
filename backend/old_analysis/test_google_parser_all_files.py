#!/usr/bin/env python3
"""Test Google parser on ALL 57 files"""

import os
import sys
import fitz
from google_parser_final_solution import parse_google_invoice

sys.stdout.reconfigure(encoding='utf-8')

# Expected totals for validation
EXPECTED_TOTALS = {
    '5297692778': 36965.00,
    '5297692787': 56626.86,
    '5297692790': -6284.42,
    '5297692799': 8578.86,
    '5297693015': 11477.33,
    '5297732883': 7756.04,
    '5297735036': 78598.69,
    '5297736216': 199789.31,
    '5297742275': 13922.17,
    '5297785878': -1.66,
    '5297786049': 4905.61,
    '5297830454': 13144.45,
    '5297833463': 14481.47,
    '5297969160': 30144.76,
    '5298021501': 59619.75,
    '5298120337': 9118.21,
    '5298130144': 7937.88,
    '5298134610': 7065.35,
    '5298142069': 139905.76,
    '5298156820': 1603456.84,
    '5298157309': 16667.47,
    '5298240989': 18889.62,
    '5298241256': 41026.71,
    '5298248238': 12697.36,
    '5298281913': -2.87,
    '5298283050': 34800.00,
    '5298361576': 8765.10,
    '5298381490': 15208.87,
    '5298382222': 21617.14,
    '5298528895': 35397.74,
    '5298615229': -442.78,
    '5298615739': 11815.89,
    '5299223229': 7708.43,
    '5299367718': 4628.51,
    '5299617709': 15252.67,
    '5300092128': 13094.36,
    '5300482566': -361.13,
    '5300584082': 9008.07,
    '5300624442': 429456.10,
    '5300646032': 7998.20,
    '5300784496': 42915.95,
    '5300840344': 27846.52,
    '5301425447': 11580.58,
    '5301461407': 29910.94,
    '5301552840': 119704.95,
    '5301655559': 4590.46,
    '5301967139': 8419.45,
    '5302009440': 17051.50,
    '5302012325': 29491.74,
    '5302293067': -184.85,
    '5302301893': 7716.03,
    '5302788327': 119996.74,
    '5302951835': -2543.65,
    '5303158396': -3.48,
    '5303644723': 7774.29,
    '5303649115': -0.39,
    '5303655373': 10674.50
}

def test_file(filename):
    """Test a single file"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    # Read text
    with fitz.open(filepath) as doc:
        text_content = ""
        for page in doc:
            text_content += page.get_text()
    
    # Parse
    items = parse_google_invoice(text_content, filepath)
    
    # Calculate total
    total = sum(item['amount'] for item in items)
    
    # Check against expected
    invoice_num = filename.replace('.pdf', '')
    expected = EXPECTED_TOTALS.get(invoice_num, 0)
    diff = abs(total - expected)
    
    return {
        'filename': filename,
        'items_count': len(items),
        'total': total,
        'expected': expected,
        'diff': diff,
        'correct': diff < 0.01,
        'items': items
    }

# Test all Google files
invoice_dir = os.path.join('..', 'Invoice for testing')
google_files = sorted([f for f in os.listdir(invoice_dir) if f.startswith('5') and f.endswith('.pdf')])

print(f"Testing {len(google_files)} Google invoice files...")
print("="*80)

results = []
correct_count = 0
multi_item_count = 0

for idx, filename in enumerate(google_files):
    result = test_file(filename)
    results.append(result)
    
    if result['correct']:
        correct_count += 1
    
    if result['items_count'] > 1:
        multi_item_count += 1
    
    # Show progress
    status = "✓" if result['correct'] else "✗"
    print(f"[{idx+1:2d}/{len(google_files)}] {status} {filename}: {result['items_count']} items, Total: {result['total']:,.2f} (Expected: {result['expected']:,.2f})")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Files tested: {len(google_files)}")
print(f"Correct totals: {correct_count} ({correct_count/len(google_files)*100:.1f}%)")
print(f"Files with multiple items: {multi_item_count} ({multi_item_count/len(google_files)*100:.1f}%)")

# Calculate average items per file
total_items = sum(r['items_count'] for r in results)
avg_items = total_items / len(results)
print(f"Average items per file: {avg_items:.2f}")

# Show files with issues
issues = [r for r in results if not r['correct']]
if issues:
    print(f"\nFiles with incorrect totals: {len(issues)}")
    for issue in issues[:5]:
        print(f"  - {issue['filename']}: Got {issue['total']:,.2f}, Expected {issue['expected']:,.2f} (diff: {issue['diff']:,.2f})")

# Show sample successful extractions
print("\nSample successful extractions:")
success_samples = [r for r in results if r['items_count'] > 5][:3]
for sample in success_samples:
    print(f"\n{sample['filename']} ({sample['items_count']} items):")
    for item in sample['items'][:3]:
        print(f"  - {item['description'][:60]}... : {item['amount']:,.2f}")