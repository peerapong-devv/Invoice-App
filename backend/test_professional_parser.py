#!/usr/bin/env python3
"""Test Google Professional Parser with problem files"""

import os
import sys
from google_parser_professional import parse_google_invoice

sys.stdout.reconfigure(encoding='utf-8')

# Test specific problem files
test_cases = {
    '5297692778.pdf': {'expected_total': 18550.72, 'expected_type': 'AP', 'should_have_pk': True},
    '5297692790.pdf': {'expected_total': -6284.42, 'expected_type': 'Non-AP', 'should_have_pk': False},
    '5297785878.pdf': {'expected_total': -1.66, 'expected_type': 'Non-AP', 'should_have_pk': False},
    '5297735036.pdf': {'expected_total': 79988.30, 'expected_type': 'Non-AP', 'should_have_pk': False}
}

invoice_dir = os.path.join('..', 'Invoice for testing')

print("TESTING GOOGLE PROFESSIONAL PARSER")
print("="*80)

all_correct = True

for filename, expected in test_cases.items():
    filepath = os.path.join(invoice_dir, filename)
    print(f"\n{filename}:")
    print(f"  Expected: Total={expected['expected_total']:.2f}, Type={expected['expected_type']}")
    
    # Parse
    items = parse_google_invoice('', filepath)
    
    if items:
        actual_total = sum(item['amount'] for item in items)
        actual_type = items[0]['invoice_type']
        has_pk = any(item.get('agency') == 'pk' for item in items)
        
        # Check total
        total_correct = abs(actual_total - expected['expected_total']) < 0.01
        type_correct = actual_type == expected['expected_type']
        pk_correct = has_pk == expected['should_have_pk']
        
        status = "✓" if (total_correct and type_correct and pk_correct) else "✗"
        
        print(f"  Actual: Total={actual_total:.2f}, Type={actual_type}, Items={len(items)} {status}")
        
        if not total_correct:
            print(f"    ERROR: Total mismatch! Diff={actual_total - expected['expected_total']:.2f}")
            all_correct = False
        
        if not type_correct:
            print(f"    ERROR: Type mismatch!")
            all_correct = False
            
        if not pk_correct:
            print(f"    ERROR: pk| field mismatch! Has pk={has_pk}, Expected={expected['should_have_pk']}")
            all_correct = False
        
        # Show items
        print("  Items:")
        for item in items[:5]:
            desc = item.get('description', '')[:60]
            print(f"    {item['line_number']}. {item['amount']:>10,.2f} - {desc}...")
            if item.get('agency'):
                print(f"       [AP] Agency: {item['agency']}, Project: {item.get('project_id')}")
        
        # Check for duplicate descriptions
        if len(items) > 1:
            descriptions = [item.get('description', '') for item in items]
            unique_descs = set(descriptions)
            if len(unique_descs) == 1:
                print("    WARNING: All items have the same description!")
    else:
        print("  ERROR: No items extracted!")
        all_correct = False

print("\n" + "="*80)
if all_correct:
    print("✓ ALL TESTS PASSED!")
else:
    print("✗ SOME TESTS FAILED!")