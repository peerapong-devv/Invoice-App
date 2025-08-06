import json

# Load the comprehensive report
with open('google_invoice_comprehensive_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Reference data from user
reference_data = {
    "5297692778.pdf": 18550.72,
    "5297692787.pdf": 18759.75,
    "5297692790.pdf": -6284.42,
    "5297692799.pdf": 8507.86,
    "5297693015.pdf": -13.42,
    "5297732883.pdf": 7621.07,
    "5297735036.pdf": -1389.61,
    "5297736216.pdf": -186.09,
    "5297742275.pdf": -292.66,
    "5297785878.pdf": -1.66,
    "5297786049.pdf": -625.00,
    "5297830454.pdf": 9664.30,
    "5297833463.pdf": -67.41,
    "5297969160.pdf": 30073.76,
    "5298021501.pdf": -372.17,
    "5298120337.pdf": 9171.35,
    "5298130144.pdf": 7871.02,
    "5298134610.pdf": 3678.31,
    "5298142069.pdf": -30.00,
    "5298156820.pdf": -625.00,
    "5298157309.pdf": 11778.71,
    "5298240989.pdf": -1662.25,
    "5298241256.pdf": 41026.71,
    "5298248238.pdf": 12607.96,
    "5298281913.pdf": -2.87,
    "5298283050.pdf": 34720.12,
    "5298361576.pdf": 6384.76,
    "5298381490.pdf": -139.29,
    "5298382222.pdf": -111.98,
    "5298528895.pdf": 35397.74,
    "5298615229.pdf": -442.78,
    "5298615739.pdf": -43.35,
    "5299223229.pdf": 7637.72,
    "5299367718.pdf": -77.25,
    "5299617709.pdf": -54.68,
    "5300092128.pdf": -55.32,
    "5300482566.pdf": -361.13,
    "5300584082.pdf": 8937.07,
    "5300624442.pdf": -209.35,
    "5300646032.pdf": -30.00,
    "5300784496.pdf": -340.77,
    "5300840344.pdf": -149.99,
    "5301425447.pdf": -141.05,
    "5301461407.pdf": -80.62,
    "5301552840.pdf": -289.36,
    "5301655559.pdf": 4519.46,
    "5301967139.pdf": 8349.09,
    "5302009440.pdf": -30.88,
    "5302012325.pdf": 29491.74,
    "5302293067.pdf": -184.85,
    "5302301893.pdf": 7646.95,
    "5302788327.pdf": -71.00,
    "5302951835.pdf": -2543.65,
    "5303158396.pdf": -3.48,
    "5303644723.pdf": 7704.10,
    "5303649115.pdf": -0.39,
    "5303655373.pdf": -100.64
}

# Calculate differences
total_reference = sum(reference_data.values())
total_current = report['summary']['total_amount_thb']

print(f"Target Total: {total_reference:,.2f} THB")
print(f"Current Total: {total_current:,.2f} THB")
print(f"Difference: {total_current - total_reference:,.2f} THB")
print(f"\nDifference is {((total_current / total_reference) - 1) * 100:.1f}% higher than target\n")

# Analyze each file
print("="*100)
print(f"{'Filename':<20} {'Reference':>15} {'Current':>15} {'Difference':>15} {'Status':<10}")
print("="*100)

differences = []
for result in report['detailed_results']:
    filename = result['filename']
    current_total = result['file_total_thb']
    ref_total = reference_data.get(filename, 0)
    diff = current_total - ref_total
    
    status = "MATCH" if abs(diff) < 0.01 else "WRONG"
    if status == "WRONG":
        differences.append({
            'filename': filename,
            'reference': ref_total,
            'current': current_total,
            'difference': diff
        })
    
    print(f"{filename:<20} {ref_total:>15,.2f} {current_total:>15,.2f} {diff:>15,.2f} {status:<10}")

print("\n" + "="*100)
print(f"\nFiles with differences: {len(differences)}")
print("\nTop 10 largest differences:")
sorted_diffs = sorted(differences, key=lambda x: abs(x['difference']), reverse=True)
for i, d in enumerate(sorted_diffs[:10], 1):
    print(f"{i}. {d['filename']}: {d['current']:,.2f} should be {d['reference']:,.2f} (diff: {d['difference']:,.2f})")

# Group by type of error
print("\nAnalysis of differences:")
positive_when_should_be_negative = [d for d in differences if d['reference'] < 0 and d['current'] > 0]
negative_when_should_be_positive = [d for d in differences if d['reference'] > 0 and d['current'] < 0]
wrong_positive = [d for d in differences if d['reference'] > 0 and d['current'] > 0 and abs(d['difference']) > 0.01]
wrong_negative = [d for d in differences if d['reference'] < 0 and d['current'] < 0 and abs(d['difference']) > 0.01]

print(f"\nPositive when should be negative: {len(positive_when_should_be_negative)} files")
for d in positive_when_should_be_negative[:5]:
    print(f"  - {d['filename']}: {d['current']:,.2f} should be {d['reference']:,.2f}")

print(f"\nNegative when should be positive: {len(negative_when_should_be_positive)} files")
for d in negative_when_should_be_positive[:5]:
    print(f"  - {d['filename']}: {d['current']:,.2f} should be {d['reference']:,.2f}")

print(f"\nWrong positive amounts: {len(wrong_positive)} files")
print(f"Wrong negative amounts: {len(wrong_negative)} files")