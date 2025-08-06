#!/usr/bin/env python3

# Test backup amounts calculation
reference_amounts = {
    "5297692778.pdf": 18482.50,
    "5297692787.pdf": 18875.62,
    "5297692790.pdf": -6284.42,
    "5297692799.pdf": 8578.86,
    "5297693015.pdf": 11477.33,
    "5297732883.pdf": 7756.04,
    "5297735036.pdf": 78598.69,
    "5297736216.pdf": 199789.31,
    "5297742275.pdf": 13922.17,
    "5297785878.pdf": -1.66,
    "5297786049.pdf": 4905.61,
    "5297830454.pdf": 13144.45,
    "5297833463.pdf": 14481.47,
    "5297969160.pdf": 30144.76,
    "5298021501.pdf": 59619.75,
    "5298120337.pdf": 9118.21,
    "5298130144.pdf": 7937.88,
    "5298134610.pdf": 7065.35,
    "5298142069.pdf": 139905.76,
    "5298156820.pdf": 801728.42,
    "5298157309.pdf": 16667.47,
    "5298240989.pdf": 18889.62,
    "5298241256.pdf": 41026.71,
    "5298248238.pdf": 12697.36,
    "5298281913.pdf": -2.87,
    "5298283050.pdf": 34800.00,
    "5298361576.pdf": 8765.10,
    "5298381490.pdf": 15208.87,
    "5298382222.pdf": 21617.14,
    "5298528895.pdf": 35397.74,
    "5298615229.pdf": -442.78,
    "5298615739.pdf": 11815.89,
    "5299223229.pdf": 7708.43,
    "5299367718.pdf": 4628.51,
    "5299617709.pdf": 15252.67,
    "5300092128.pdf": 13094.36,
    "5300482566.pdf": -361.13,
    "5300584082.pdf": 9008.07,
    "5300624442.pdf": 214728.05,
    "5300646032.pdf": 7998.20,
    "5300784496.pdf": 42915.95,
    "5300840344.pdf": 27846.52,
    "5301425447.pdf": 11580.58,
    "5301461407.pdf": 29910.94,
    "5301552840.pdf": 119704.95,
    "5301655559.pdf": 4590.46,
    "5301967139.pdf": 8419.45,
    "5302009440.pdf": 17051.50,
    "5302012325.pdf": 29491.74,
    "5302293067.pdf": -184.85,
    "5302301893.pdf": 7716.03,
    "5302788327.pdf": 119996.74,
    "5302951835.pdf": -2543.65,
    "5303158396.pdf": -3.48,
    "5303644723.pdf": 7774.29,
    "5303649115.pdf": -0.39,
    "5303655373.pdf": 10674.50
}

print("BACKUP DATA CALCULATION")
print("=" * 60)

total = sum(reference_amounts.values())
print(f"Calculated total: {total:,.2f} THB")
print(f"User expects: 2,440,679.74 THB")
print(f"Difference: {2440679.74 - total:,.2f} THB")

print(f"\nNumber of files: {len(reference_amounts)}")

# Show largest amounts
sorted_amounts = sorted(reference_amounts.items(), key=lambda x: x[1], reverse=True)
print(f"\nTop 10 largest amounts:")
for filename, amount in sorted_amounts[:10]:
    print(f"  {filename}: {amount:,.2f} THB")

print(f"\nTop 5 negative amounts:")
negative_amounts = [(f, a) for f, a in sorted_amounts if a < 0]
for filename, amount in negative_amounts[:5]:
    print(f"  {filename}: {amount:,.2f} THB")