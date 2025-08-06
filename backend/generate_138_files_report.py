#!/usr/bin/env python3
"""
Generate detailed JSON report for all 138 invoice files
"""

import os
import fitz
import json
from datetime import datetime

# Import the parsers
from facebook_parser_enhanced_ap import parse_facebook_invoice
from google_parser_smart_final import parse_google_invoice
from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed

def generate_detailed_report():
    """Generate detailed report for all 138 files"""
    
    print("Generating detailed report for all 138 invoice files...")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    invoice_dir = "../Invoice for testing"
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(invoice_dir) if f.endswith('.pdf')]
    pdf_files.sort()
    
    # Initialize report structure
    report = {
        "generated": datetime.now().isoformat(),
        "summary": {
            "total_files": len(pdf_files),
            "processed": 0,
            "errors": 0,
            "by_platform": {
                "TikTok": {"files": 0, "items": 0, "amount": 0.0},
                "Facebook": {"files": 0, "items": 0, "amount": 0.0},
                "Google": {"files": 0, "items": 0, "amount": 0.0},
                "Unknown": {"files": 0, "items": 0, "amount": 0.0}
            },
            "by_type": {
                "AP": {"files": 0, "items": 0, "amount": 0.0},
                "Non-AP": {"files": 0, "items": 0, "amount": 0.0}
            }
        },
        "files": {}
    }
    
    # Process each file
    for idx, filename in enumerate(pdf_files, 1):
        print(f"Processing [{idx}/{len(pdf_files)}]: {filename}")
        filepath = os.path.join(invoice_dir, filename)
        
        try:
            # Read PDF
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            # Determine platform and parse - check filename first
            platform = "Unknown"
            items = []
            
            if filename.startswith('THTT'):
                platform = "TikTok"
                items = parse_tiktok_invoice_detailed(text, filename)
            elif filename.startswith('5'):
                platform = "Google"
                items = parse_google_invoice(text, filename)
            elif filename.startswith('24'):
                platform = "Facebook"
                items = parse_facebook_invoice(text, filename)
            # Fallback to content checking
            elif 'TikTok' in text or 'ByteDance' in text:
                platform = "TikTok"
                items = parse_tiktok_invoice_detailed(text, filename)
            elif 'Google' in text and 'Ads' in text:
                platform = "Google"
                items = parse_google_invoice(text, filename)
            elif 'Facebook' in text or 'Meta' in text:
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
            
            # Update summary statistics
            report["summary"]["processed"] += 1
            report["summary"]["by_platform"][platform]["files"] += 1
            report["summary"]["by_platform"][platform]["items"] += len(items)
            report["summary"]["by_platform"][platform]["amount"] += total_amount
            
            if invoice_type in ["AP", "Non-AP"]:
                report["summary"]["by_type"][invoice_type]["files"] += 1
                report["summary"]["by_type"][invoice_type]["items"] += len(items)
                report["summary"]["by_type"][invoice_type]["amount"] += total_amount
            
            # Store file details
            report["files"][filename] = {
                "platform": platform,
                "invoice_type": invoice_type,
                "invoice_number": items[0].get('invoice_number', 'Unknown') if items else 'Unknown',
                "total_items": len(items),
                "total_amount": total_amount,
                "items": []
            }
            
            # Store all items with full details
            for item in items:
                item_data = {
                    "line_number": item.get('line_number'),
                    "amount": item.get('amount', 0),
                    "description": item.get('description', '')
                }
                
                # Add AP fields if present
                if invoice_type == "AP":
                    item_data.update({
                        "agency": item.get('agency'),
                        "project_id": item.get('project_id'),
                        "project_name": item.get('project_name'),
                        "objective": item.get('objective'),
                        "period": item.get('period'),
                        "campaign_id": item.get('campaign_id')
                    })
                
                report["files"][filename]["items"].append(item_data)
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            report["summary"]["errors"] += 1
            report["files"][filename] = {
                "platform": platform if 'platform' in locals() else "Unknown",
                "error": str(e)
            }
    
    # Calculate grand totals
    grand_total = sum(
        platform_data["amount"] 
        for platform_data in report["summary"]["by_platform"].values()
    )
    report["summary"]["grand_total"] = grand_total
    
    # Save report
    output_file = "all_138_files_detailed_report.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total files: {report['summary']['total_files']}")
    print(f"Processed: {report['summary']['processed']}")
    print(f"Errors: {report['summary']['errors']}")
    
    print("\nBy Platform:")
    for platform, data in report["summary"]["by_platform"].items():
        if data["files"] > 0:
            print(f"  {platform}: {data['files']} files, {data['items']} items, {data['amount']:,.2f} THB")
    
    print("\nBy Type:")
    for inv_type, data in report["summary"]["by_type"].items():
        if data["files"] > 0:
            print(f"  {inv_type}: {data['files']} files, {data['items']} items, {data['amount']:,.2f} THB")
    
    print(f"\nGrand Total: {grand_total:,.2f} THB")
    print(f"\nReport saved to: {output_file}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    generate_detailed_report()