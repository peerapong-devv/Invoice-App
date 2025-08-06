#!/usr/bin/env python3
"""Check Google invoice totals"""

import json

# Load report
with open('all_138_files_detailed_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Expected Google totals
EXPECTED_GOOGLE_TOTALS = {
    '5297692778': 18482.50,
    '5297692787': 29304.33,
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
    '5298156820': 801728.42,
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
    '5300624442': 214728.05,
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

# Check Google files
print("Checking Google invoices...")
print("="*80)

total_expected = 0
total_actual = 0
differences = []

for filename, file_data in report['files'].items():
    if file_data.get('platform') == 'Google':
        invoice_number = filename.replace('.pdf', '')
        
        if invoice_number in EXPECTED_GOOGLE_TOTALS:
            expected = EXPECTED_GOOGLE_TOTALS[invoice_number]
            actual = file_data.get('total_amount', 0)
            total_expected += expected
            total_actual += actual
            
            diff = actual - expected
            if abs(diff) > 0.01:
                differences.append({
                    'file': filename,
                    'expected': expected,
                    'actual': actual,
                    'diff': diff
                })

# Show differences
if differences:
    print(f"\nFound {len(differences)} files with differences:")
    print("-"*80)
    for d in sorted(differences, key=lambda x: abs(x['diff']), reverse=True):
        print(f"{d['file']}: Expected {d['expected']:,.2f}, Got {d['actual']:,.2f}, Diff: {d['diff']:+,.2f}")

print(f"\n{'='*80}")
print(f"Total Expected: {total_expected:,.2f}")
print(f"Total Actual: {total_actual:,.2f}")
print(f"Total Difference: {total_actual - total_expected:+,.2f}")

# Check if all expected files are present
expected_files = set(EXPECTED_GOOGLE_TOTALS.keys())
actual_files = set()

for filename, file_data in report['files'].items():
    if file_data.get('platform') == 'Google':
        invoice_number = filename.replace('.pdf', '')
        actual_files.add(invoice_number)

missing = expected_files - actual_files
if missing:
    print(f"\nMissing files: {missing}")

extra = actual_files - expected_files
if extra:
    print(f"\nExtra files: {extra}")