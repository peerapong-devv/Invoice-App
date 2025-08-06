#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime
sys.path.append('backend')

from backup_google_parser import parse_google_text

def test_google_detailed_json():
    """Test Google parser and generate detailed JSON report"""
    
    # All 57 files from corrected user data
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
    
    print("GENERATING DETAILED GOOGLE PARSER JSON REPORT")
    print("=" * 60)
    print(f"Testing {len(all_files)} files")
    print()
    
    # Prepare report structure
    report = {
        "report_metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": len(all_files),
            "parser_version": "backup_google_parser_corrected_user_data"
        },
        "summary": {
            "successful_files": 0,
            "error_files": 0,
            "total_records": 0,
            "campaign_records": 0,
            "refund_records": 0,
            "fee_records": 0,
            "total_amount_thb": 0.0
        },
        "detailed_results": [],
        "error_files": [],
        "sample_records": []
    }
    
    total_amount = 0
    
    for filename in sorted(all_files):
        try:
            records = parse_google_text("", filename, "Google")
            
            if records:
                file_total = sum(record.get('total', 0) for record in records)
                total_amount += file_total
                
                # Count record types
                campaign_count = sum(1 for r in records if r.get('item_type') == 'Campaign')
                refund_count = sum(1 for r in records if r.get('item_type') == 'Refund') 
                fee_count = sum(1 for r in records if r.get('item_type') == 'Fee')
                
                # Add to detailed results
                file_result = {
                    "filename": filename,
                    "status": "success",
                    "records_count": len(records),
                    "file_total_thb": file_total,
                    "campaign_count": campaign_count,
                    "refund_count": refund_count,
                    "fee_count": fee_count,
                    "invoice_id": records[0].get('invoice_id', ''),
                    "invoice_type": records[0].get('invoice_type', ''),
                    "parser_used": "backup_corrected"
                }
                
                report["detailed_results"].append(file_result)
                report["summary"]["successful_files"] += 1
                report["summary"]["total_records"] += len(records)
                report["summary"]["campaign_records"] += campaign_count
                report["summary"]["refund_records"] += refund_count
                report["summary"]["fee_records"] += fee_count
                
                # Add sample record (first 10 files)
                if len(report["sample_records"]) < 10:
                    sample_record = {
                        "filename": filename,
                        "sample_record": records[0]  # First record as sample
                    }
                    report["sample_records"].append(sample_record)
                
                print(f"{filename:<20}: {file_total:>12,.2f} THB ({len(records)} records) - {records[0].get('invoice_type', 'Unknown')}")
                
            else:
                # No records returned
                error_result = {
                    "filename": filename,
                    "error": "No records returned",
                    "status": "no_records"
                }
                report["error_files"].append(error_result)
                report["summary"]["error_files"] += 1
                print(f"{filename:<20}: NO RECORDS")
            
        except Exception as e:
            # Exception occurred
            error_result = {
                "filename": filename,
                "error": str(e),
                "status": "exception"
            }
            report["error_files"].append(error_result)
            report["summary"]["error_files"] += 1
            print(f"{filename:<20}: ERROR - {str(e)}")
    
    # Update final summary
    report["summary"]["total_amount_thb"] = total_amount
    
    print()
    print("=" * 60)
    print(f"SUMMARY:")
    print(f"  Successful files: {report['summary']['successful_files']}")
    print(f"  Error files: {report['summary']['error_files']}")
    print(f"  Total records: {report['summary']['total_records']}")
    print(f"  Campaign records: {report['summary']['campaign_records']}")
    print(f"  Refund records: {report['summary']['refund_records']}")
    print(f"  Fee records: {report['summary']['fee_records']}")
    print(f"  Total amount: {total_amount:,.2f} THB")
    print(f"  Expected: 2,362,684.79 THB")
    print(f"  Match: {'YES' if abs(total_amount - 2362684.79) < 0.01 else 'NO'}")
    
    # Save JSON report
    json_filename = 'google_invoice_detailed_report.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed JSON report saved to: {json_filename}")
    return report

if __name__ == "__main__":
    report = test_google_detailed_json()