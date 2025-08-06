#!/usr/bin/env python3

# Data from user's table (70 files total)
user_data = {
    "5303655373": 10674.50,
    "5303649115": -0.39,
    "5303644723": 7774.29,
    "5303158396": -3.48,
    "5302951835": -2543.65,
    "5302788327": 119996.74,
    "5302301893": 7716.03,
    "5302293067": -184.85,
    "5302012325": 29491.74,
    "5302009440": 17051.50,
    "5301967139": 8419.45,
    "5301655559": 4590.46,
    "5301552840": 119704.95,
    "5301461407": 29910.94,
    "5301425447": 11580.58,
    "5300840344": 27846.52,
    "5300784496": 42915.95,
    "5300646032": 7998.20,
    "5300624442": 214728.05,
    "5300584082": 9008.07,
    "5300482566": -361.13,
    "5300092128": 13094.36,
    "5299617709": 15252.67,
    "5299367718": 4628.51,
    "5299223229": 7708.43,
    "5298615739": 11815.89,
    "5298615229": -442.78,
    "5298528895": 35397.74,
    "5298382222": 21617.14,
    "5298381490": 15208.87,
    "5298361576": 8765.10,
    "5298283050": 34800.00,
    "5298281913": -2.87,
    "5298248238": 12697.36,
    "5298241256": 41026.71,
    "5298240989": 18889.62,
    "5298157309": 16667.47,
    "5298156820": 801728.42,
    "5298142069": 139905.76,
    "5298134610": 7065.35,
    "5298130144": 7937.88,
    "5298120337": 9118.21,
    "5298021501": 59619.75,
    "5297969160": 30144.76,
    "5297833463": 14481.47,
    "5297830454": 13144.45,
    "5297786049": 4905.61,
    "5297785878": -1.66,
    "5297742275": 13922.17,
    "5297736216": 199789.31,
    "5297735036": 78598.69,
    "5297732883": 7756.04,
    "5297693015": 11477.33,
    "5297692799": 8578.86,
    "5297692790": -6284.42,
    "5297692787": 18875.62,
    "5297692778": 18482.50,
    # Additional files from user data
    "5199895377": 78445.66,
    "5199788940": -2.4,
    "5198588158": -42.15,
    "5198552898": -0.97,
    "5198408089": -65.75,
    "5198378760": -42.76,
    "5197810576": -23.58,
    "5197780138": -53.77,
    "5197380816": -2.05,
    "5197118207": -213.01,
    "5196293202": -4.02,
    "5196116721": -0.08,
    "5195741580": -0.17
}

# Data from backup (57 files)
backup_data = {
    "5297692778": 18482.50,
    "5297692787": 18875.62,
    "5297692790": -6284.42,
    "5297692799": 8578.86,
    "5297693015": 11477.33,
    "5297732883": 7756.04,
    "5297735036": 78598.69,
    "5297736216": 199789.31,
    "5297742275": 13922.17,
    "5297785878": -1.66,
    "5297786049": 4905.61,
    "5297830454": 13144.45,
    "5297833463": 14481.47,
    "5297969160": 30144.76,
    "5298021501": 59619.75,
    "5298120337": 9118.21,
    "5298130144": 7937.88,
    "5298134610": 7065.35,
    "5298142069": 139905.76,
    "5298156820": 801728.42,
    "5298157309": 16667.47,
    "5298240989": 18889.62,
    "5298241256": 41026.71,
    "5298248238": 12697.36,
    "5298281913": -2.87,
    "5298283050": 34800.00,
    "5298361576": 8765.10,
    "5298381490": 15208.87,
    "5298382222": 21617.14,
    "5298528895": 35397.74,
    "5298615229": -442.78,
    "5298615739": 11815.89,
    "5299223229": 7708.43,
    "5299367718": 4628.51,
    "5299617709": 15252.67,
    "5300092128": 13094.36,
    "5300482566": -361.13,
    "5300584082": 9008.07,
    "5300624442": 214728.05,
    "5300646032": 7998.20,
    "5300784496": 42915.95,
    "5300840344": 27846.52,
    "5301425447": 11580.58,
    "5301461407": 29910.94,
    "5301552840": 119704.95,
    "5301655559": 4590.46,
    "5301967139": 8419.45,
    "5302009440": 17051.50,
    "5302012325": 29491.74,
    "5302293067": -184.85,
    "5302301893": 7716.03,
    "5302788327": 119996.74,
    "5302951835": -2543.65,
    "5303158396": -3.48,
    "5303644723": 7774.29,
    "5303649115": -0.39,
    "5303655373": 10674.50
}

print("COMPARISON: USER DATA vs BACKUP DATA")
print("=" * 80)

# Calculate totals
user_total = sum(user_data.values())
backup_total = sum(backup_data.values())

print(f"User data total: {user_total:,.2f} THB ({len(user_data)} files)")
print(f"Backup data total: {backup_total:,.2f} THB ({len(backup_data)} files)")
print(f"Difference: {user_total - backup_total:,.2f} THB")
print(f"Expected by user: 2,440,679.74 THB")
print()

# Find differences in common files
print("DIFFERENCES IN COMMON FILES:")
print("-" * 80)
differences = []
for doc_id in backup_data:
    if doc_id in user_data:
        user_amount = user_data[doc_id]
        backup_amount = backup_data[doc_id]
        if abs(user_amount - backup_amount) > 0.01:
            diff = user_amount - backup_amount
            differences.append((doc_id, user_amount, backup_amount, diff))
            print(f"{doc_id}: User={user_amount:,.2f}, Backup={backup_amount:,.2f}, Diff={diff:,.2f}")

if not differences:
    print("✅ No differences found in common files!")
else:
    print(f"\n❌ Found {len(differences)} files with differences")

# Find files in user data but not in backup
print(f"\nFILES IN USER DATA BUT NOT IN BACKUP:")
print("-" * 80)
missing_from_backup = []
for doc_id in user_data:
    if doc_id not in backup_data:
        missing_from_backup.append((doc_id, user_data[doc_id]))
        print(f"{doc_id}: {user_data[doc_id]:,.2f} THB")

if missing_from_backup:
    missing_total = sum(amount for _, amount in missing_from_backup)
    print(f"\nTotal from missing files: {missing_total:,.2f} THB")
    print(f"This explains the difference: {missing_total:,.2f} THB")

print(f"\nCORRECTED TOTAL IF WE ADD MISSING FILES:")
corrected_total = backup_total + sum(amount for _, amount in missing_from_backup)
print(f"Backup total: {backup_total:,.2f} THB")
print(f"Missing files total: {sum(amount for _, amount in missing_from_backup):,.2f} THB") 
print(f"Corrected total: {corrected_total:,.2f} THB")
print(f"Expected: 2,440,679.74 THB")
print(f"Final difference: {corrected_total - 2440679.74:,.2f} THB")