#!/usr/bin/env python3
import sys
import os
sys.path.append('backend')

from backup_google_parser import parse_google_text

def test_comprehensive_google():
    """Test all Google files with simplified parser"""
    
    # All Google files
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
    
    print("TESTING SIMPLIFIED GOOGLE PARSER")
    print("=" * 60)
    print(f"Testing {len(all_files)} files")
    print()
    
    total_amount = 0
    records_count = 0
    processed_files = 0
    
    for filename in all_files:
        try:
            records = parse_google_text("", filename, "Google")
            
            if records:
                file_total = sum(record.get('total', 0) for record in records)
                total_amount += file_total
                records_count += len(records)
                print(f"{filename:20}: {file_total:>12,.2f} THB ({len(records)} records)")
            else:
                print(f"{filename:20}: NO RECORDS")
            
            processed_files += 1
            
        except Exception as e:
            print(f"{filename:20}: ERROR - {str(e)}")
    
    print()
    print("=" * 60)
    print(f"RESULTS:")
    print(f"  Files processed: {processed_files}")
    print(f"  Total records: {records_count}")
    print(f"  Total amount: {total_amount:,.2f} THB")
    print()
    
    # Compare with expected
    expected = 313085.90
    difference = total_amount - expected
    
    print(f"COMPARISON:")
    print(f"  Calculated total: {total_amount:,.2f} THB")
    print(f"  Expected total: {expected:,.2f} THB")
    print(f"  Difference: {difference:,.2f} THB")
    
    if abs(difference) < 0.01:
        print(f"  STATUS: ✅ PERFECT MATCH!")
    else:
        print(f"  STATUS: ❌ MISMATCH")
    
    return total_amount == expected

if __name__ == "__main__":
    success = test_comprehensive_google()
    print(f"\nFinal Result: {'SUCCESS' if success else 'FAILED'}")