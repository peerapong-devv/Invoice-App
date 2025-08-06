#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime
sys.path.append('backend')

from google_parser_complete import parse_google_invoice_complete

def test_google_complete_detailed():
    """Generate comprehensive JSON report with detailed extraction for AP invoices"""
    
    invoice_dir = "Invoice for testing"
    
    # Test files that should be AP (have pk| patterns)
    test_files = [
        "5297692778.pdf",  # AP invoice
        "5298248238.pdf",  # AP invoice with pk patterns
        "5298361576.pdf",  # AP invoice
        "5297692790.pdf",  # Credit note (Non-AP)
        "5298156820.pdf"   # Non-AP invoice
    ]
    
    print("COMPREHENSIVE GOOGLE PARSER COMPLETE TEST")
    print("=" * 60)
    print("Testing detailed extraction with google_parser_complete.py")
    print()
    
    all_results = []
    total_amount = 0
    
    for i, filename in enumerate(test_files, 1):
        print(f"[{i}/{len(test_files)}] Testing: {filename}")
        
        file_path = os.path.join(invoice_dir, filename)
        if not os.path.exists(file_path):
            print(f"  File not found: {file_path}")
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
                
                # Detailed analysis
                ap_records = [r for r in records if r.get('invoice_type') == 'AP']
                non_ap_records = [r for r in records if r.get('invoice_type') != 'AP']
                
                result = {
                    "filename": filename,
                    "status": "success",
                    "file_total": file_total,
                    "records_count": len(records),
                    "invoice_type": records[0].get('invoice_type', 'Unknown'),
                    "ap_records_count": len(ap_records),
                    "non_ap_records_count": len(non_ap_records),
                    "detailed_records": []
                }
                
                # Add detailed record information
                for j, record in enumerate(records[:10], 1):  # First 10 records per file
                    detailed_record = {
                        "line_number": j,
                        "item_type": record.get('item_type'),
                        "description": record.get('description', '')[:100] + ('...' if len(str(record.get('description', ''))) > 100 else ''),
                        "amount": record.get('total'),
                        "agency": record.get('agency'),
                        "project_id": record.get('project_id'),
                        "project_name": record.get('project_name'),
                        "objective": record.get('objective'),
                        "period": record.get('period'),
                        "campaign_id": record.get('campaign_id')
                    }
                    result["detailed_records"].append(detailed_record)
                
                all_results.append(result)
                
                print(f"  SUCCESS: {file_total:,.2f} THB")
                print(f"  Type: {records[0].get('invoice_type')}")
                print(f"  Records: {len(records)} total")
                
                # Show AP field extraction
                ap_with_details = [r for r in ap_records if r.get('project_id') and r.get('project_id') != 'Unknown']
                if ap_with_details:
                    print(f"  AP Records with Details: {len(ap_with_details)}")
                    sample_ap = ap_with_details[0]
                    print(f"    Sample: Agency={sample_ap.get('agency')}, Project={sample_ap.get('project_id')}, Campaign={sample_ap.get('campaign_id')}")
                elif ap_records:
                    print(f"  AP Records without Details: {len(ap_records)}")
                print()
                
            else:
                print("  ERROR: No records returned")
                print()
                
        except Exception as e:
            print(f"  EXCEPTION: {str(e)}")
            print()
    
    # Generate comprehensive report
    report = {
        "test_metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "parser_used": "google_parser_complete.py",
            "test_files_count": len(test_files),
            "successful_files": len(all_results)
        },
        "summary": {
            "total_amount": total_amount,
            "files_tested": len(all_results),
            "ap_invoices": len([r for r in all_results if r.get('invoice_type') == 'AP']),
            "non_ap_invoices": len([r for r in all_results if r.get('invoice_type') != 'AP']),
            "total_records": sum(r.get('records_count', 0) for r in all_results),
            "ap_records_with_details": sum(
                len([rec for rec in r.get('detailed_records', []) 
                     if rec.get('project_id') and rec.get('project_id') != 'Unknown'])
                for r in all_results if r.get('invoice_type') == 'AP'
            )
        },
        "detailed_results": all_results
    }
    
    # Save comprehensive JSON report
    report_filename = 'google_parser_complete_detailed_report.json'
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print("FINAL SUMMARY:")
    print(f"Total Amount: {total_amount:,.2f} THB")
    print(f"Files Processed: {len(all_results)}")
    print(f"AP Invoices: {report['summary']['ap_invoices']}")
    print(f"Non-AP Invoices: {report['summary']['non_ap_invoices']}")
    print(f"Total Records: {report['summary']['total_records']}")
    print(f"AP Records with Details: {report['summary']['ap_records_with_details']}")
    print(f"\nDetailed report saved: {report_filename}")
    
    return report

if __name__ == "__main__":
    test_google_complete_detailed()