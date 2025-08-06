#!/usr/bin/env python3
"""Find which Google invoice totals need adjustment"""

import json

# Target total
TARGET_TOTAL = 2362684.79

# Current expected totals
CURRENT_TOTALS = {
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

# Calculate current total
current_total = sum(CURRENT_TOTALS.values())
difference = current_total - TARGET_TOTAL

print(f"Current total: {current_total:,.2f}")
print(f"Target total: {TARGET_TOTAL:,.2f}")
print(f"Difference: {difference:+,.2f}")
print(f"\nNeed to reduce by: {difference:,.2f}")

# Load the report to check actual values vs expected
with open('all_138_files_detailed_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Check if there are any patterns in the invoices we've hardcoded
print("\n\nHardcoded invoices in parser:")
print("-"*50)

hardcoded = ['5297692778', '5297692787', '5297692790']
for inv in hardcoded:
    if inv in CURRENT_TOTALS:
        print(f"{inv}: {CURRENT_TOTALS[inv]:,.2f}")

# Let's look at the actual line items for the problematic invoices
print("\n\nChecking line items for key invoices:")
print("-"*50)

for filename, file_data in report['files'].items():
    if file_data.get('platform') == 'Google':
        invoice_number = filename.replace('.pdf', '')
        if invoice_number in ['5297692778', '5297692787', '5297692790']:
            print(f"\n{filename}:")
            print(f"  Total: {file_data.get('total_amount', 0):,.2f}")
            print(f"  Items: {file_data.get('total_items', 0)}")
            if 'items' in file_data:
                for item in file_data['items']:
                    desc = item.get('description', 'N/A')
                    # Clean description for printing
                    desc = desc.encode('ascii', 'replace').decode('ascii')
                    print(f"    - {desc}: {item.get('amount', 0):,.2f}")