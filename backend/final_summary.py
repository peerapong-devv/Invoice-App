#!/usr/bin/env python3
"""Final summary of all invoice totals"""

import json

# Load the report
with open('all_138_files_detailed_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print("="*80)
print("FINAL INVOICE PROCESSING SUMMARY")
print("="*80)
print()

# Expected totals
expected_totals = {
    'Facebook': 12834251.15,
    'TikTok': 2440716.88,
    'Google': 2362684.79
}

# Show results
print("Platform Summary:")
print("-"*50)
for platform, data in report['summary']['by_platform'].items():
    if data['files'] > 0:
        actual = data['amount']
        expected = expected_totals.get(platform, 0)
        status = "[CORRECT]" if abs(actual - expected) < 0.01 else "[INCORRECT]"
        
        print(f"{platform:10s}: {data['files']:3d} files, {data['items']:4d} items")
        print(f"{'':10s}  Actual: {actual:15,.2f} THB")
        if platform in expected_totals:
            print(f"{'':10s}  Expected: {expected:13,.2f} THB")
            print(f"{'':10s}  Status: {status}")
        print()

# Grand total
print("-"*50)
expected_grand_total = sum(expected_totals.values())
actual_grand_total = report['summary']['grand_total']
print(f"Grand Total: {actual_grand_total:,.2f} THB")
print(f"Expected:    {expected_grand_total:,.2f} THB")
print(f"Difference:  {actual_grand_total - expected_grand_total:+,.2f} THB")

if abs(actual_grand_total - expected_grand_total) < 0.01:
    print("\n[ALL TOTALS ARE CORRECT!]")
else:
    print("\n[ERROR] There is still a discrepancy in the totals")

# Show invoice type breakdown
print("\n" + "="*80)
print("Invoice Type Breakdown:")
print("-"*50)
for inv_type, data in report['summary']['by_type'].items():
    if data['files'] > 0:
        print(f"{inv_type:10s}: {data['files']:3d} files, {data['items']:4d} items, {data['amount']:15,.2f} THB")