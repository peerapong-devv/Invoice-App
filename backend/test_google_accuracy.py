#!/usr/bin/env python3
"""
Test Google parser accuracy against expected values
"""

import fitz
import os
from google_parser_extract import parse_google_invoice

# Expected values from user
google_expected = {
    '5303655373': 10674.50, '5303649115': -0.39, '5303644723': 7774.29, '5303158396': -3.48,
    '5302951835': -2543.65, '5302788327': 119996.74, '5302301893': 7716.03, '5302293067': -184.85,
    '5302012325': 29491.74, '5302009440': 17051.50, '5301967139': 8419.45, '5301655559': 4590.46,
    '5301552840': 119704.95, '5301461407': 29910.94, '5301425447': 11580.58, '5300840344': 27846.52,
    '5300784496': 42915.95, '5300646032': 7998.20, '5300624442': 214728.05, '5300584082': 9008.07,
    '5300482566': -361.13, '5300092128': 13094.36, '5299617709': 15252.67, '5299367718': 4628.51,
    '5299223229': 7708.43, '5298615739': 11815.89, '5298615229': -442.78, '5298528895': 35397.74,
    '5298382222': 21617.14, '5298381490': 15208.87, '5298361576': 8765.10, '5298283050': 34800.00,
    '5298281913': -2.87, '5298248238': 12697.36, '5298241256': 41026.71, '5298240989': 18889.62,
    '5298157309': 16667.47, '5298156820': 801728.42, '5298142069': 139905.76, '5298134610': 7065.35,
    '5298130144': 7937.88, '5298120337': 9118.21, '5298021501': 59619.75, '5297969160': 30144.76,
    '5297833463': 14481.47, '5297830454': 13144.45, '5297786049': 4905.61, '5297785878': -1.66,
    '5297742275': 13922.17, '5297736216': 199789.31, '5297735036': 78598.69, '5297732883': 7756.04,
    '5297693015': 11477.33, '5297692799': 8578.86, '5297692790': -6284.42, '5297692787': 18875.62,
    '5297692778': 18482.50
}

print("Testing Google Parser Accuracy")
print("="*60)

invoice_dir = "../Invoice for testing"
total_expected = 0
total_extracted = 0
perfect_count = 0
missing_files = []

for doc_num, expected_amount in google_expected.items():
    filename = f"{doc_num}.pdf"
    filepath = os.path.join(invoice_dir, filename)
    
    if not os.path.exists(filepath):
        missing_files.append(filename)
        continue
    
    try:
        with fitz.open(filepath) as doc:
            text = ''
            for page in doc:
                text += page.get_text()
        
        items = parse_google_invoice(text, filename)
        extracted_amount = sum(item['amount'] for item in items)
        
        # Check accuracy
        if abs(extracted_amount - expected_amount) < 0.01:
            perfect_count += 1
            status = "PERFECT"
        else:
            status = f"  Diff: {extracted_amount - expected_amount:,.2f}"
        
        print(f"\n{filename}:")
        print(f"  Expected: {expected_amount:,.2f}")
        print(f"  Extracted: {extracted_amount:,.2f}")
        print(f"  {status}")
        
        total_expected += expected_amount
        total_extracted += extracted_amount
        
    except Exception as e:
        print(f"\n{filename}: ERROR - {str(e)}")

print(f"\n{'='*60}")
print(f"SUMMARY:")
print(f"Total files: {len(google_expected)}")
print(f"Perfect extraction: {perfect_count}/{len(google_expected) - len(missing_files)}")
print(f"Total expected: {total_expected:,.2f} THB")
print(f"Total extracted: {total_extracted:,.2f} THB")
print(f"Overall accuracy: {(total_extracted/total_expected*100) if total_expected != 0 else 0:.2f}%")

if missing_files:
    print(f"\nMissing files: {len(missing_files)}")
    for f in missing_files[:5]:
        print(f"  - {f}")