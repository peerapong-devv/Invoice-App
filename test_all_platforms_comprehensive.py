#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime
sys.path.append('backend')

# Import all parsers from the app.py configuration
from google_parser_complete import parse_google_invoice_complete

def classify_invoice_file(filename):
    """Classify invoice file by platform based on filename patterns"""
    filename_lower = filename.lower()
    
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

def parse_facebook_text_mock(text_content, filename, platform):
    """Mock Facebook parser - replace with actual when available"""
    return [{
        "platform": "Facebook",
        "filename": filename,
        "invoice_type": "Mock",
        "total": 0,
        "description": "Facebook parser not implemented in test"
    }]

def parse_tiktok_text_mock(text_content, filename, platform):
    """Mock TikTok parser - replace with actual when available"""
    return [{
        "platform": "TikTok", 
        "filename": filename,
        "invoice_type": "Mock",
        "total": 0,
        "description": "TikTok parser not implemented in test"
    }]

def test_all_platforms_comprehensive():
    """Test all invoice files across all platforms and generate comprehensive report"""
    
    invoice_dir = "Invoice for testing"
    
    if not os.path.exists(invoice_dir):
        print(f"Error: Directory not found: {invoice_dir}")
        return
    
    # Get all PDF files
    all_files = [f for f in os.listdir(invoice_dir) if f.endswith('.pdf')]
    all_files.sort()
    
    print("COMPREHENSIVE ALL-PLATFORM INVOICE TEST")
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
        print(f"{platform}: {len(files)} files")
    print()
    
    # Initialize comprehensive report
    report = {
        "test_metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_directory": invoice_dir,
            "total_files": len(all_files),
            "description": "Comprehensive test of all invoice files across Google, Facebook, and TikTok platforms"
        },
        "platform_summary": {
            "Google": {"files": len(platform_files["Google"]), "successful": 0, "total_amount": 0.0},
            "Facebook": {"files": len(platform_files["Facebook"]), "successful": 0, "total_amount": 0.0},
            "TikTok": {"files": len(platform_files["TikTok"]), "successful": 0, "total_amount": 0.0},
            "Unknown": {"files": len(platform_files["Unknown"]), "successful": 0, "total_amount": 0.0}
        },
        "detailed_results": {
            "Google": [],
            "Facebook": [],
            "TikTok": [],
            "Unknown": []
        },
        "overall_summary": {
            "total_files": len(all_files),
            "successful_files": 0,
            "error_files": 0,
            "total_amount_all_platforms": 0.0,
            "total_records": 0
        },
        "error_files": []
    }
    
    # Test each platform
    for platform in ["Google", "Facebook", "TikTok", "Unknown"]:
        if not platform_files[platform]:
            continue
            
        print(f"TESTING {platform.upper()} PLATFORM:")
        print("-" * 50)
        
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
                
                # Parse based on platform
                records = []
                if platform == "Google":
                    records = parse_google_invoice_complete(text_content, filename)
                elif platform == "Facebook":
                    records = parse_facebook_text_mock(text_content, filename, platform)
                elif platform == "TikTok":
                    records = parse_tiktok_text_mock(text_content, filename, platform)
                else:
                    records = [{"platform": "Unknown", "filename": filename, "total": 0}]
                
                if records:
                    file_total = sum(r.get('total', 0) for r in records if r.get('total') is not None)
                    platform_total += file_total
                    platform_successful += 1
                    
                    # Create file result
                    file_result = {
                        "filename": filename,
                        "status": "success",
                        "file_total": file_total,
                        "records_count": len(records),
                        "invoice_type": records[0].get('invoice_type', 'Unknown') if records else 'Unknown',
                        "platform": platform
                    }
                    
                    # Add detailed info for Google (since it's working)
                    if platform == "Google":
                        ap_records = [r for r in records if r.get('invoice_type') == 'AP']
                        ap_with_details = [r for r in ap_records 
                                         if r.get('project_id') and r.get('project_id') not in ['Unknown', None]]
                        
                        file_result.update({
                            "ap_records_count": len(ap_records),
                            "ap_with_details_count": len(ap_with_details),
                            "campaign_records": len([r for r in records if r.get('item_type') == 'Campaign']),
                            "refund_records": len([r for r in records if r.get('item_type') == 'Refund']),
                            "is_credit_note": file_total < 0
                        })
                    
                    report["detailed_results"][platform].append(file_result)
                    
                    # Display result
                    status_info = f"{file_total:>12,.2f} THB | {len(records):2d} records"
                    if platform == "Google":
                        invoice_type = records[0].get('invoice_type', 'Unknown')
                        status_info += f" | {invoice_type}"
                        if file_total < 0:
                            status_info += " (Credit)"
                    
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
        
        print(f"Platform Total: {platform_total:,.2f} THB ({platform_successful}/{len(platform_files[platform])} files)")
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
    report_filename = 'all_platforms_comprehensive_test_report.json'
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Display final summary
    print("=" * 80)
    print("FINAL COMPREHENSIVE SUMMARY:")
    print("=" * 80)
    print(f"📁 Total Files Found: {len(all_files)}")
    print(f"✅ Successfully Processed: {total_successful}")
    print(f"❌ Error Files: {len(report['error_files'])}")
    print(f"💰 Total Amount (All Platforms): {total_amount_all:,.2f} THB")
    print()
    
    print("PLATFORM BREAKDOWN:")
    print("-" * 50)
    for platform, summary in report["platform_summary"].items():
        if summary["files"] > 0:
            success_rate = (summary["successful"] / summary["files"]) * 100
            print(f"{platform:>8}: {summary['successful']:2d}/{summary['files']:2d} files ({success_rate:5.1f}%) | {summary['total_amount']:>12,.2f} THB")
    
    print()
    print("GOOGLE PLATFORM VALIDATION:")
    print("-" * 30)
    google_total = report["platform_summary"]["Google"]["total_amount"]
    expected_google = 2362684.79
    google_diff = abs(google_total - expected_google)
    google_match = "✅ CORRECT" if google_diff < 0.01 else "❌ INCORRECT"
    print(f"Google Total: {google_total:,.2f} THB")
    print(f"Expected:     {expected_google:,.2f} THB") 
    print(f"Difference:   {google_diff:,.2f} THB")
    print(f"Status:       {google_match}")
    
    if len(report["error_files"]) > 0:
        print()
        print("ERROR FILES:")
        print("-" * 20)
        for error in report["error_files"]:
            print(f"  {error['filename']} ({error['platform']}): {error['error']}")
    
    print()
    print(f"📄 Comprehensive report saved: {report_filename}")
    
    return report

if __name__ == "__main__":
    test_all_platforms_comprehensive()