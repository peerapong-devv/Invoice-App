#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime
sys.path.append('backend')

from google_parser_complete import parse_google_invoice_complete

def test_all_57_google_files_detailed():
    """Test all 57 Google invoice files and generate comprehensive JSON report with every line"""
    
    invoice_dir = "Invoice for testing"
    
    # All 57 files from user's corrected data
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
    
    print("COMPREHENSIVE GOOGLE PARSER TEST - ALL 57 FILES")
    print("=" * 70)
    print(f"Processing {len(all_files)} Google invoice files...")
    print("Generating detailed JSON with every extracted line...")
    print()
    
    # Report structure
    report = {
        "report_metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "parser_version": "google_parser_complete.py",
            "total_files": len(all_files),
            "description": "Comprehensive test of all 57 Google invoice files with detailed line-by-line extraction"
        },
        "summary": {
            "successful_files": 0,
            "error_files": 0,
            "total_records": 0,
            "ap_invoices": 0,
            "non_ap_invoices": 0,
            "credit_notes": 0,
            "total_amount_thb": 0.0,
            "ap_records_with_details": 0,
            "campaign_records": 0,
            "refund_records": 0,
            "fee_records": 0
        },
        "detailed_results": [],
        "error_files": []
    }
    
    total_amount = 0
    
    for i, filename in enumerate(sorted(all_files), 1):
        print(f"[{i:2d}/{len(all_files)}] Processing: {filename}")
        
        file_path = os.path.join(invoice_dir, filename)
        if not os.path.exists(file_path):
            error_result = {
                "filename": filename,
                "status": "file_not_found",
                "error": f"File not found: {file_path}"
            }
            report["error_files"].append(error_result)
            report["summary"]["error_files"] += 1
            print(f"          ERROR: File not found")
            continue
            
        try:
            # Extract text using PyMuPDF (same as app.py)
            import fitz
            with fitz.open(file_path) as doc:
                text_content = ""
                for page in doc:
                    text_content += page.get_text() + "\n"
            
            # Parse with google_parser_complete
            records = parse_google_invoice_complete(text_content, filename)
            
            if records:
                file_total = sum(r.get('total', 0) for r in records if r.get('total') is not None)
                total_amount += file_total
                
                # Analyze record types
                campaign_records = [r for r in records if r.get('item_type') == 'Campaign']
                refund_records = [r for r in records if r.get('item_type') == 'Refund']
                fee_records = [r for r in records if r.get('item_type') == 'Fee']
                
                # Count AP records with detailed extraction
                ap_with_details = [r for r in records 
                                 if r.get('invoice_type') == 'AP' 
                                 and r.get('project_id') 
                                 and r.get('project_id') not in ['Unknown', None]]
                
                # Determine invoice classification
                invoice_type = records[0].get('invoice_type', 'Unknown')
                is_credit_note = file_total < 0
                
                # Create detailed file result
                file_result = {
                    "filename": filename,
                    "status": "success",
                    "file_total_thb": file_total,
                    "records_count": len(records),
                    "invoice_type": invoice_type,
                    "is_credit_note": is_credit_note,
                    "campaign_records_count": len(campaign_records),
                    "refund_records_count": len(refund_records),
                    "fee_records_count": len(fee_records),
                    "ap_records_with_details_count": len(ap_with_details),
                    "invoice_id": records[0].get('invoice_id', ''),
                    "all_extracted_records": []
                }
                
                # Add every single extracted record
                for j, record in enumerate(records, 1):
                    detailed_record = {
                        "line_number": j,
                        "item_type": record.get('item_type'),
                        "description": record.get('description', ''),
                        "amount_thb": record.get('total'),
                        "agency": record.get('agency'),
                        "project_id": record.get('project_id'),
                        "project_name": record.get('project_name'),
                        "objective": record.get('objective'),
                        "period": record.get('period'),
                        "campaign_id": record.get('campaign_id'),
                        "invoice_type": record.get('invoice_type'),
                        "invoice_id": record.get('invoice_id'),
                        "source_filename": record.get('source_filename'),
                        "platform": record.get('platform')
                    }
                    file_result["all_extracted_records"].append(detailed_record)
                
                report["detailed_results"].append(file_result)
                
                # Update summary counters
                report["summary"]["successful_files"] += 1
                report["summary"]["total_records"] += len(records)
                report["summary"]["campaign_records"] += len(campaign_records)
                report["summary"]["refund_records"] += len(refund_records)
                report["summary"]["fee_records"] += len(fee_records)
                report["summary"]["ap_records_with_details"] += len(ap_with_details)
                
                if invoice_type == "AP":
                    report["summary"]["ap_invoices"] += 1
                else:
                    report["summary"]["non_ap_invoices"] += 1
                    
                if is_credit_note:
                    report["summary"]["credit_notes"] += 1
                
                # Display progress
                status_info = f"{invoice_type}"
                if is_credit_note:
                    status_info += " (Credit Note)"
                if len(ap_with_details) > 0:
                    status_info += f" - {len(ap_with_details)} detailed AP records"
                    
                print(f"          SUCCESS: {file_total:>12,.2f} THB | {len(records):2d} records | {status_info}")
                
            else:
                error_result = {
                    "filename": filename,
                    "status": "no_records",
                    "error": "No records returned from parser"
                }
                report["error_files"].append(error_result)
                report["summary"]["error_files"] += 1
                print(f"          ERROR: No records returned")
                
        except Exception as e:
            error_result = {
                "filename": filename,
                "status": "exception",
                "error": str(e)
            }
            report["error_files"].append(error_result)
            report["summary"]["error_files"] += 1
            print(f"          EXCEPTION: {str(e)}")
    
    # Update final summary
    report["summary"]["total_amount_thb"] = total_amount
    
    # Save comprehensive JSON report
    report_filename = 'google_all_57_files_comprehensive_report.json'
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 70)
    print("FINAL SUMMARY:")
    print(f"  Total Files Processed: {report['summary']['successful_files']}/{len(all_files)}")
    print(f"  Error Files: {report['summary']['error_files']}")
    print(f"  Total Amount: {total_amount:,.2f} THB")
    print(f"  Expected Amount: 2,362,684.79 THB")
    print(f"  Difference: {abs(total_amount - 2362684.79):,.2f} THB")
    match_status = "YES" if abs(total_amount - 2362684.79) < 0.01 else "NO"
    print(f"  Match: {match_status}")
    print()
    print(f"  AP Invoices: {report['summary']['ap_invoices']}")
    print(f"  Non-AP Invoices: {report['summary']['non_ap_invoices']}")
    print(f"  Credit Notes: {report['summary']['credit_notes']}")
    print(f"  Total Records Extracted: {report['summary']['total_records']}")
    print(f"  Campaign Records: {report['summary']['campaign_records']}")
    print(f"  Refund Records: {report['summary']['refund_records']}")
    print(f"  Fee Records: {report['summary']['fee_records']}")
    print(f"  AP Records with Details: {report['summary']['ap_records_with_details']}")
    print()
    print(f"📄 Comprehensive JSON report saved: {report_filename}")
    print(f"   Contains detailed line-by-line extraction for all {len(all_files)} files")
    
    return report

if __name__ == "__main__":
    test_all_57_google_files_detailed()