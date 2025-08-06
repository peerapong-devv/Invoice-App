#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime
sys.path.append('backend')

# Import real working parsers
from google_parser_complete import parse_google_invoice_complete
from facebook_parser_complete import parse_facebook_invoice_complete
from working_tiktok_parser_lookup import parse_tiktok_invoice_lookup

def classify_invoice_file(filename):
    """Classify invoice file by platform based on filename patterns"""
    # Google: Files starting with 5 (529*, 530*)
    if filename.startswith('5') and filename.endswith('.pdf'):
        return "Google"
    
    # Facebook: Files starting with 246 (but not THTT)
    elif filename.startswith('246') and filename.endswith('.pdf') and not filename.startswith('THTT'):
        return "Facebook"
        
    # TikTok: Files starting with THTT
    elif filename.startswith('THTT') and filename.endswith('.pdf'):
        return "TikTok"
    
    else:
        return "Unknown"

def test_all_platforms_with_real_parsers():
    """Test all platforms using real working parsers"""
    
    invoice_dir = "Invoice for testing"
    
    if not os.path.exists(invoice_dir):
        print(f"Error: Directory not found: {invoice_dir}")
        return
    
    # Get all PDF files
    all_files = [f for f in os.listdir(invoice_dir) if f.endswith('.pdf')]
    all_files.sort()
    
    print("COMPREHENSIVE ALL-PLATFORM TEST WITH REAL PARSERS")
    print("=" * 80)
    print(f"Testing directory: {invoice_dir}")
    print(f"Total PDF files found: {len(all_files)}")
    print()
    
    # Classify files by platform
    platform_files = {
        "Google": [],
        "Facebook": [],
        "TikTok": [],
        "Unknown": []
    }
    
    for filename in all_files:
        platform = classify_invoice_file(filename)
        platform_files[platform].append(filename)
    
    print("FILE CLASSIFICATION BY PLATFORM:")
    print("-" * 40)
    for platform, files in platform_files.items():
        print(f"{platform:>8}: {len(files):2d} files")
    print()
    
    # Initialize comprehensive report
    report = {
        "test_metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_directory": invoice_dir,
            "total_files": len(all_files),
            "description": "Comprehensive test using real working parsers for all platforms",
            "parsers_used": {
                "Google": "google_parser_complete.py",
                "Facebook": "facebook_parser_complete.py", 
                "TikTok": "working_tiktok_parser_lookup.py"
            }
        },
        "platform_summary": {},
        "detailed_results": {},
        "overall_summary": {
            "total_files": len(all_files),
            "successful_files": 0,
            "error_files": 0,
            "total_amount_all_platforms": 0.0,
            "total_records": 0
        },
        "error_files": []
    }
    
    # Initialize platform summaries
    for platform in ["Google", "Facebook", "TikTok", "Unknown"]:
        report["platform_summary"][platform] = {
            "files": len(platform_files[platform]),
            "successful": 0,
            "total_amount": 0.0,
            "ap_invoices": 0,
            "non_ap_invoices": 0,
            "credit_notes": 0,
            "detailed_records": 0
        }
        report["detailed_results"][platform] = []
    
    # Test each platform
    for platform in ["Google", "Facebook", "TikTok", "Unknown"]:
        if not platform_files[platform]:
            continue
            
        print(f"TESTING {platform.upper()} PLATFORM:")
        print(f"Parser: {report['test_metadata']['parsers_used'].get(platform, 'None')}")
        print("-" * 60)
        
        platform_total = 0.0
        platform_successful = 0
        
        for i, filename in enumerate(platform_files[platform], 1):
            print(f"[{i:2d}/{len(platform_files[platform])}] {filename}")
            
            file_path = os.path.join(invoice_dir, filename)
            
            try:
                # Extract text using PyMuPDF
                import fitz
                with fitz.open(file_path) as doc:
                    text_content = ""
                    for page in doc:
                        text_content += page.get_text() + "\n"
                
                # Parse based on platform using real parsers
                records = []
                if platform == "Google":
                    records = parse_google_invoice_complete(text_content, filename)
                elif platform == "Facebook":
                    records = parse_facebook_invoice_complete(text_content, filename)
                elif platform == "TikTok":
                    records = parse_tiktok_invoice_lookup(text_content, filename)
                else:
                    # Unknown platform - just create a placeholder
                    records = []
                
                if records:
                    # Handle different field names across parsers
                    file_total = 0
                    for r in records:
                        amount = r.get('total') or r.get('amount') or 0
                        if amount is not None:
                            file_total += amount
                    
                    platform_total += file_total
                    platform_successful += 1
                    
                    # Analyze record types and invoice classification
                    invoice_type = records[0].get('invoice_type', 'Unknown') if records else 'Unknown'
                    is_credit_note = file_total < 0
                    
                    # Count different record types
                    ap_records = [r for r in records if r.get('invoice_type') == 'AP']
                    campaign_records = [r for r in records if r.get('item_type') == 'Campaign']
                    refund_records = [r for r in records if r.get('item_type') == 'Refund']
                    fee_records = [r for r in records if r.get('item_type') == 'Fee']
                    
                    # Count detailed extraction success
                    detailed_count = 0
                    if platform == "Google":
                        detailed_count = len([r for r in ap_records 
                                           if r.get('project_id') and r.get('project_id') not in ['Unknown', None]])
                    elif platform == "Facebook":
                        detailed_count = len([r for r in records 
                                           if r.get('line_item_description') and len(str(r.get('line_item_description', ''))) > 10])
                    elif platform == "TikTok":
                        detailed_count = len([r for r in records 
                                           if r.get('ad_account_name') and r.get('ad_account_name') != 'Unknown'])
                    
                    # Create file result
                    file_result = {
                        "filename": filename,
                        "status": "success",
                        "file_total": file_total,
                        "records_count": len(records),
                        "invoice_type": invoice_type,
                        "is_credit_note": is_credit_note,
                        "platform": platform,
                        "campaign_records": len(campaign_records),
                        "refund_records": len(refund_records),
                        "fee_records": len(fee_records),
                        "ap_records": len(ap_records),
                        "detailed_extraction_count": detailed_count
                    }
                    
                    report["detailed_results"][platform].append(file_result)
                    
                    # Update platform counters
                    if invoice_type == "AP":
                        report["platform_summary"][platform]["ap_invoices"] += 1
                    else:
                        report["platform_summary"][platform]["non_ap_invoices"] += 1
                        
                    if is_credit_note:
                        report["platform_summary"][platform]["credit_notes"] += 1
                        
                    report["platform_summary"][platform]["detailed_records"] += detailed_count
                    
                    # Display result
                    status_info = f"{file_total:>12,.2f} THB | {len(records):2d} records"
                    if invoice_type != "Unknown":
                        status_info += f" | {invoice_type}"
                    if is_credit_note:
                        status_info += " (Credit)"
                    if detailed_count > 0:
                        status_info += f" | {detailed_count} detailed"
                    
                    print(f"          SUCCESS: {status_info}")
                    
                else:
                    print(f"          ERROR: No records returned")
                    error_result = {
                        "filename": filename,
                        "platform": platform,
                        "error": "No records returned",
                        "status": "no_records"
                    }
                    report["error_files"].append(error_result)
                    
            except Exception as e:
                print(f"          EXCEPTION: {str(e)}")
                error_result = {
                    "filename": filename,
                    "platform": platform,
                    "error": str(e),
                    "status": "exception"
                }
                report["error_files"].append(error_result)
        
        # Update platform summary
        report["platform_summary"][platform]["successful"] = platform_successful
        report["platform_summary"][platform]["total_amount"] = platform_total
        
        print(f"Platform Total: {platform_total:>15,.2f} THB ({platform_successful}/{len(platform_files[platform])} files)")
        if platform_successful > 0:
            avg_per_file = platform_total / platform_successful
            print(f"Average per file: {avg_per_file:>13,.2f} THB")
        print()
    
    # Calculate overall summary
    total_successful = sum(summary["successful"] for summary in report["platform_summary"].values())
    total_amount_all = sum(summary["total_amount"] for summary in report["platform_summary"].values())
    total_records = sum(len(results) for results in report["detailed_results"].values())
    
    report["overall_summary"].update({
        "successful_files": total_successful,
        "error_files": len(report["error_files"]),
        "total_amount_all_platforms": total_amount_all,
        "total_records": total_records
    })
    
    # Save comprehensive report
    report_filename = 'all_platforms_real_parsers_comprehensive_report.json'
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Display final summary
    print("=" * 80)
    print("FINAL COMPREHENSIVE SUMMARY:")
    print("=" * 80)
    print(f"Total Files Found: {len(all_files)}")
    print(f"Successfully Processed: {total_successful}")
    print(f"Error Files: {len(report['error_files'])}")
    print(f"Total Amount (All Platforms): {total_amount_all:,.2f} THB")
    print()
    
    print("PLATFORM BREAKDOWN:")
    print("-" * 70)
    header = f"{'Platform':>8} | {'Files':>5} | {'Success':>7} | {'Amount (THB)':>15} | {'AP':>3} | {'Non-AP':>6} | {'Credit':>6} | {'Detailed':>8}"
    print(header)
    print("-" * 70)
    
    for platform, summary in report["platform_summary"].items():
        if summary["files"] > 0:
            success_rate = f"{summary['successful']}/{summary['files']}"
            print(f"{platform:>8} | {summary['files']:5d} | {success_rate:>7} | {summary['total_amount']:>15,.2f} | "
                  f"{summary['ap_invoices']:3d} | {summary['non_ap_invoices']:6d} | "
                  f"{summary['credit_notes']:6d} | {summary['detailed_records']:8d}")
    
    print()
    print("VALIDATION RESULTS:")
    print("-" * 30)
    
    # Google validation
    google_total = report["platform_summary"]["Google"]["total_amount"]
    expected_google = 2362684.79
    google_diff = abs(google_total - expected_google)
    google_match = "CORRECT" if google_diff < 0.01 else "INCORRECT"
    print(f"Google Total: {google_total:>15,.2f} THB")
    print(f"Expected:     {expected_google:>15,.2f} THB") 
    print(f"Difference:   {google_diff:>15,.2f} THB")
    print(f"Status:       {google_match}")
    
    # Show detailed extraction success
    print()
    print("DETAILED EXTRACTION SUCCESS:")
    print("-" * 40)
    for platform, summary in report["platform_summary"].items():
        if summary["files"] > 0 and summary["detailed_records"] > 0:
            print(f"{platform}: {summary['detailed_records']} records with detailed data extraction")
    
    if len(report["error_files"]) > 0:
        print()
        print("ERROR FILES:")
        print("-" * 20)
        for error in report["error_files"]:
            print(f"  {error['filename']} ({error['platform']}): {error['error']}")
    
    print()
    print(f"Comprehensive report saved: {report_filename}")
    
    return report

if __name__ == "__main__":
    test_all_platforms_with_real_parsers()