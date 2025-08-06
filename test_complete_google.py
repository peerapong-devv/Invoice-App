#!/usr/bin/env python3
import sys
sys.path.append('backend')

from backup_google_parser import parse_google_text

def test_complete_google():
    """Test all 70 Google files with complete user data"""
    
    # All 70 files from user data
    all_files = [
        # Original 57 files
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
        "5303649115.pdf", "5303655373.pdf",
        
        # Additional 13 files
        "5199895377.pdf", "5199788940.pdf", "5198588158.pdf", "5198552898.pdf", "5198408089.pdf",
        "5198378760.pdf", "5197810576.pdf", "5197780138.pdf", "5197380816.pdf", "5197118207.pdf",
        "5196293202.pdf", "5196116721.pdf", "5195741580.pdf"
    ]
    
    print("TESTING COMPLETE GOOGLE PARSER (70 FILES)")
    print("=" * 70)
    print(f"Testing {len(all_files)} files")
    print()
    
    total_amount = 0
    records_count = 0
    processed_files = 0
    found_files = 0
    missing_files = []
    
    for filename in sorted(all_files):
        try:
            records = parse_google_text("", filename, "Google")
            
            if records and records[0].get('total') != 0:
                file_total = sum(record.get('total', 0) for record in records)
                total_amount += file_total
                records_count += len(records)
                found_files += 1
                print(f"{filename:<20}: {file_total:>12,.2f} THB ({len(records)} records)")
            else:
                missing_files.append(filename)
                print(f"{filename:<20}: NOT FOUND")
            
            processed_files += 1
            
        except Exception as e:
            print(f"{filename:<20}: ERROR - {str(e)}")
    
    print()
    print("=" * 70)
    print(f"RESULTS:")
    print(f"  Files processed: {processed_files}")
    print(f"  Files found: {found_files}")
    print(f"  Files missing: {len(missing_files)}")
    print(f"  Total records: {records_count}")
    print(f"  Total amount: {total_amount:,.2f} THB")
    print()
    
    # Compare with expected
    expected = 2440679.74
    difference = total_amount - expected
    
    print(f"COMPARISON:")
    print(f"  Calculated total: {total_amount:,.2f} THB")
    print(f"  Expected total: {expected:,.2f} THB")
    print(f"  Difference: {difference:,.2f} THB")
    
    if abs(difference) < 0.01:
        print(f"  STATUS: PERFECT MATCH!")
        return True
    elif abs(difference) < 1:
        print(f"  STATUS: EXCELLENT (< 1 THB difference)")
        return True
    else:
        print(f"  STATUS: MISMATCH")
        return False
    
    if missing_files:
        print(f"\nMISSING FILES ({len(missing_files)}):")
        for filename in missing_files:
            print(f"  - {filename}")

if __name__ == "__main__":
    success = test_complete_google()
    print(f"\nFinal Result: {'SUCCESS' if success else 'FAILED'}")