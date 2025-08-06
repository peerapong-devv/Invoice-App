#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze all Google invoices to understand their structure"""

import fitz
import re
import sys
import json
import os

sys.stdout.reconfigure(encoding='utf-8')

# Expected totals for validation
EXPECTED_TOTALS = {
    '5303655373': 10674.50, '5303649115': -0.39, '5303644723': 7774.29,
    '5303158396': -3.48, '5302951835': -2543.65, '5302788327': 119996.74,
    '5302301893': 7716.03, '5302293067': -184.85, '5302012325': 29491.74,
    '5302009440': 17051.50, '5301967139': 8419.45, '5301655559': 4590.46,
    '5301552840': 119704.95, '5301461407': 29910.94, '5301425447': 11580.58,
    '5300840344': 27846.52, '5300784496': 42915.95, '5300646032': 7998.20,
    '5300624442': 214728.05, '5300584082': 9008.07, '5300482566': -361.13,
    '5300092128': 13094.36, '5299617709': 15252.67, '5299367718': 4628.51,
    '5299223229': 7708.43, '5298615739': 11815.89, '5298615229': -442.78,
    '5298528895': 35397.74, '5298382222': 21617.14, '5298381490': 15208.87,
    '5298361576': 8765.10, '5298283050': 34800.00, '5298281913': -2.87,
    '5298248238': 12697.36, '5298241256': 41026.71, '5298240989': 18889.62,
    '5298157309': 16667.47, '5298156820': 801728.42, '5298142069': 139905.76,
    '5298134610': 7065.35, '5298130144': 7937.88, '5298120337': 9118.21,
    '5298021501': 59619.75, '5297969160': 30144.76, '5297833463': 14481.47,
    '5297830454': 13144.45, '5297786049': 4905.61, '5297785878': -1.66,
    '5297742275': 13922.17, '5297736216': 199789.31, '5297735036': 78598.69,
    '5297732883': 7756.04, '5297693015': 11477.33, '5297692799': 8578.86,
    '5297692790': -6284.42, '5297692787': 18875.62, '5297692778': 18482.50
}

# Analyze a specific invoice
def analyze_invoice(filepath):
    invoice_number = os.path.basename(filepath).replace('.pdf', '')
    expected_total = EXPECTED_TOTALS.get(invoice_number, 0)
    
    with fitz.open(filepath) as doc:
        all_text = ''
        page_texts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            all_text += page_text
            page_texts.append(page_text)
        
        # Clean text
        all_text = all_text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
        lines = all_text.split('\n')
        
        # Find amounts
        amount_pattern = re.compile(r'^\s*(-?\d{1,3}(?:,\d{3})*\.?\d{2})\s*$')
        amounts = []
        for i, line in enumerate(lines):
            match = amount_pattern.match(line.strip())
            if match:
                amount = float(match.group(1).replace(',', ''))
                if abs(amount) >= 0.01:  # Include all amounts
                    amounts.append({
                        'amount': amount,
                        'line_index': i,
                        'context': get_context(lines, i)
                    })
        
        # Calculate sum
        sum_amounts = sum(a['amount'] for a in amounts if 100 < abs(a['amount']) < 500000)
        
        # Check for campaign/line item indicators
        has_campaigns = any(keyword in all_text for keyword in ['แคมเปญ', 'Campaign', 'การคลิก', 'Click', 'Impression'])
        has_pk_pattern = 'pk|' in all_text or 'pk｜' in all_text or 'p k |' in all_text
        has_multiple_items = len([a for a in amounts if 100 < abs(a['amount']) < 500000]) > 1
        
        return {
            'invoice_number': invoice_number,
            'expected_total': expected_total,
            'num_pages': len(doc),
            'num_amounts': len(amounts),
            'sum_amounts': sum_amounts,
            'has_campaigns': has_campaigns,
            'has_pk_pattern': has_pk_pattern,
            'has_multiple_items': has_multiple_items,
            'potential_line_items': len([a for a in amounts if 100 < abs(a['amount']) < 500000]),
            'sample_amounts': [a['amount'] for a in amounts[:5]]
        }

def get_context(lines, index, context_size=3):
    """Get context around a line"""
    start = max(0, index - context_size)
    end = min(len(lines), index + context_size + 1)
    return lines[start:end]

# Analyze all Google invoices
invoice_dir = '../Invoice for testing'
google_files = [f for f in os.listdir(invoice_dir) if f.startswith('5') and f.endswith('.pdf')]
google_files.sort()

results = []
for filename in google_files:
    filepath = os.path.join(invoice_dir, filename)
    result = analyze_invoice(filepath)
    results.append(result)
    
    if result['has_multiple_items'] and result['potential_line_items'] > 1:
        print(f"\n{filename}: {result['potential_line_items']} potential line items")
        print(f"  Expected: {result['expected_total']:,.2f}")
        print(f"  Sum: {result['sum_amounts']:,.2f}")
        print(f"  Has campaigns: {result['has_campaigns']}")
        print(f"  Has pk pattern: {result['has_pk_pattern']}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Total Google invoices: {len(results)}")
print(f"Invoices with multiple potential line items: {sum(1 for r in results if r['potential_line_items'] > 1)}")
print(f"Invoices with campaign keywords: {sum(1 for r in results if r['has_campaigns'])}")
print(f"Invoices with pk patterns: {sum(1 for r in results if r['has_pk_pattern'])}")

# Save detailed results
with open('google_invoice_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)