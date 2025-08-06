#!/usr/bin/env python3
"""
Test all 138 invoice files and generate detailed JSON report
"""

import os
import fitz
import json
from datetime import datetime
from facebook_google_fixed_parsers import parse_facebook_invoice, parse_google_invoice
from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed

def test_all_invoice_files():
    """Test all 138 invoice files in the Invoice for testing folder"""
    
    print("="*100)
    print("TESTING ALL 138 INVOICE FILES")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    # Get all PDF files
    invoice_folder = "../Invoice for testing"
    pdf_files = [f for f in os.listdir(invoice_folder) if f.endswith('.pdf')]
    pdf_files.sort()
    
    print(f"\nFound {len(pdf_files)} PDF files to process")
    
    all_results = {}
    summary_stats = {
        "total_files": len(pdf_files),
        "processed": 0,
        "errors": 0,
        "by_platform": {
            "TikTok": {"files": 0, "items": 0, "amount": 0},
            "Facebook": {"files": 0, "items": 0, "amount": 0},
            "Google": {"files": 0, "items": 0, "amount": 0},
            "Unknown": {"files": 0, "items": 0, "amount": 0}
        },
        "by_type": {
            "AP": {"files": 0, "items": 0, "amount": 0},
            "Non-AP": {"files": 0, "items": 0, "amount": 0}
        }
    }
    
    # Process each file
    for idx, filename in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] Processing: {filename}")
        
        try:
            # Read PDF
            filepath = os.path.join(invoice_folder, filename)
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            # Determine platform and parse
            platform = "Unknown"
            items = []
            
            if filename.startswith('THTT') or "tiktok" in text.lower() or "bytedance" in text.lower():
                platform = "TikTok"
                items = parse_tiktok_invoice_detailed(text, filename)
            elif filename.startswith('5') or ("google" in text.lower() and "ads" in text.lower()):
                platform = "Google"
                items = parse_google_invoice(text, filename)
            elif filename.startswith('24') or "facebook" in text.lower() or "meta" in text.lower():
                platform = "Facebook"
                items = parse_facebook_invoice(text, filename)
            
            # Calculate totals
            total_amount = sum(item.get('amount', 0) for item in items)
            
            # Determine invoice type
            invoice_type = "Unknown"
            if items:
                if any(item.get('invoice_type') == 'AP' for item in items):
                    invoice_type = "AP"
                elif any(item.get('invoice_type') == 'Non-AP' for item in items):
                    invoice_type = "Non-AP"
            
            # Store detailed results
            all_results[filename] = {
                "platform": platform,
                "invoice_type": invoice_type,
                "total_items": len(items),
                "total_amount": total_amount,
                "items": items
            }
            
            # Update summary statistics
            summary_stats["processed"] += 1
            summary_stats["by_platform"][platform]["files"] += 1
            summary_stats["by_platform"][platform]["items"] += len(items)
            summary_stats["by_platform"][platform]["amount"] += total_amount
            
            if invoice_type in ["AP", "Non-AP"]:
                summary_stats["by_type"][invoice_type]["files"] += 1
                summary_stats["by_type"][invoice_type]["items"] += len(items)
                summary_stats["by_type"][invoice_type]["amount"] += total_amount
            
            print(f"  Platform: {platform}")
            print(f"  Type: {invoice_type}")
            print(f"  Items: {len(items)}")
            print(f"  Total: {total_amount:,.2f} THB")
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            all_results[filename] = {
                "error": str(e),
                "platform": "Unknown",
                "invoice_type": "Unknown"
            }
            summary_stats["errors"] += 1
    
    # Print summary
    print("\n" + "="*100)
    print("SUMMARY STATISTICS")
    print("="*100)
    
    print(f"\nTotal files processed: {summary_stats['processed']}/{summary_stats['total_files']}")
    print(f"Errors: {summary_stats['errors']}")
    
    print("\nBy Platform:")
    for platform, stats in summary_stats["by_platform"].items():
        if stats["files"] > 0:
            print(f"  {platform:10}: {stats['files']:3} files, {stats['items']:5} items, {stats['amount']:15,.2f} THB")
    
    print("\nBy Type:")
    for inv_type, stats in summary_stats["by_type"].items():
        if stats["files"] > 0:
            print(f"  {inv_type:10}: {stats['files']:3} files, {stats['items']:5} items, {stats['amount']:15,.2f} THB")
    
    # Save detailed report
    report = {
        "generated": datetime.now().isoformat(),
        "summary": summary_stats,
        "files": all_results
    }
    
    output_file = "all_138_files_detailed_report.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[COMPLETED] Detailed report saved to: {output_file}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Also save a simplified CSV summary
    csv_file = "all_138_files_summary.csv"
    with open(csv_file, "w", encoding='utf-8') as f:
        f.write("filename,platform,invoice_type,total_items,total_amount\n")
        for filename, data in all_results.items():
            if 'error' not in data:
                f.write(f"{filename},{data['platform']},{data['invoice_type']},{data['total_items']},{data['total_amount']:.2f}\n")
    
    print(f"Summary CSV saved to: {csv_file}")
    
    return all_results

if __name__ == "__main__":
    test_all_invoice_files()