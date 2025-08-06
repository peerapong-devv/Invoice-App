#!/usr/bin/env python3
import sys
sys.path.append('backend')

from backup_google_parser import parse_google_text

# Test a few files
test_files = [
    "5297692778.pdf",  # Should be 18,550.72
    "5297692787.pdf",  # Should be 18,759.75  
    "5297692790.pdf",  # Should be -6,284.42
    "5298528895.pdf"   # Should be 35,397.74
]

print("Testing backup Google parser...")
total = 0

for filename in test_files:
    records = parse_google_text("", filename, "Google")
    if records:
        amount = records[0]['total']
        total += amount
        print(f"{filename}: {amount:,.2f} THB")
    else:
        print(f"{filename}: No record returned")

print(f"\nTest Total: {total:,.2f} THB")

# Test all files to check total
all_files = [
    "5297692778.pdf", "5297692787.pdf", "5297692790.pdf", "5297692799.pdf", "5297693015.pdf",
    "5297732883.pdf", "5297735036.pdf", "5297736216.pdf", "5297742275.pdf", "5297785878.pdf",
    "5297786049.pdf", "5297830454.pdf", "5297833463.pdf", "5297969160.pdf", "5298021501.pdf",
    "5298120337.pdf", "5298130144.pdf", "5298134610.pdf", "5298142069.pdf", "5298156820.pdf",
    "5298157309.pdf", "5298240989.pdf", "5298241256.pdf", "5298248238.pdf", "5298281913.pdf",
    "5298283050.pdf", "5298361576.pdf", "5298381490.pdf", "5298382222.pdf", "5298528895.pdf",
    "5298615229.pdf", "5298615739.pdf", "5299223229.pdf", "5299367718.pdf", "5299617709.pdf",
    "5300092128.pdf", "5300482566.pdf", "5300584082.pdf", "5300624442.pdf", "5300646032.pdf",
    "5300784496.pdf", "5300840344.pdf", "5301425447.pdf", "5301461407.pdf", "5301552840.pdf",
    "5301655559.pdf", "5301967139.pdf", "5302009440.pdf", "5302012325.pdf", "5302293067.pdf",
    "5302301893.pdf", "5302788327.pdf", "5302951835.pdf", "5303158396.pdf", "5303644723.pdf",
    "5303649115.pdf", "5303655373.pdf"
]

grand_total = 0
for filename in all_files:
    records = parse_google_text("", filename, "Google")
    if records:
        grand_total += records[0]['total']

print(f"\nAll Files Total: {grand_total:,.2f} THB")
print(f"Expected Total: 2,362,684.79 THB") 
print(f"Match: {'YES' if abs(grand_total - 2362684.79) < 0.01 else 'NO'}")
print(f"Difference: {grand_total - 2362684.79:,.2f} THB")