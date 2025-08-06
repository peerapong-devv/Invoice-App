#!/usr/bin/env python3
"""
Detailed test report for all invoice parsers
"""

import fitz
import json
from datetime import datetime
from facebook_google_fixed_parsers import parse_facebook_invoice, parse_google_invoice
from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed

def generate_detailed_report():
    """Generate detailed test report with all extracted data"""
    
    print("="*100)
    print("DETAILED INVOICE PARSER TEST REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    # Test files
    test_files = {
        "TikTok": "THTT202502215482-Prakit Holdings Public Company Limited-Invoice.pdf",
        "Facebook AP": "246543739.pdf", 
        "Facebook Non-AP": "246617307.pdf",
        "Google Non-AP": "5303655373.pdf"
    }
    
    all_results = {}
    
    for platform, filename in test_files.items():
        print(f"\n{'='*80}")
        print(f"TESTING: {platform}")
        print(f"File: {filename}")
        print("="*80)
        
        try:
            # Read file
            filepath = f"../Invoice for testing/{filename}"
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            # Parse based on platform
            if "TikTok" in platform:
                items = parse_tiktok_invoice_detailed(text, filename)
            elif "Facebook" in platform:
                items = parse_facebook_invoice(text, filename)
            elif "Google" in platform:
                items = parse_google_invoice(text, filename)
            else:
                items = []
            
            # Store results
            all_results[platform] = {
                "filename": filename,
                "total_items": len(items),
                "total_amount": sum(item.get('amount', 0) for item in items),
                "items": items
            }
            
            # Print summary
            print(f"\n[SUMMARY]")
            print(f"Total items extracted: {len(items)}")
            print(f"Total amount: {all_results[platform]['total_amount']:,.2f} THB")
            
            # Determine invoice type
            has_ap_fields = any(item.get('agency') == 'pk' for item in items) if items else False
            invoice_type = "AP" if has_ap_fields else "Non-AP"
            print(f"Invoice type: {invoice_type}")
            
            # For AP invoices, show field statistics
            if has_ap_fields:
                print(f"\n[AP FIELD STATISTICS]")
                ap_fields = ['agency', 'project_id', 'project_name', 'objective', 'period', 'campaign_id']
                
                for field in ap_fields:
                    filled_count = sum(1 for item in items if item.get(field) and item.get(field) not in ['Unknown', 'N/A', None])
                    percentage = (filled_count / len(items) * 100) if items else 0
                    print(f"{field:15}: {filled_count:3}/{len(items):3} ({percentage:6.2f}%)")
            
            # Show first 5 items in detail
            print(f"\n[FIRST 5 ITEMS - DETAILED]")
            for i, item in enumerate(items[:5], 1):
                print(f"\n--- Item {i} ---")
                print(f"Line number: {item.get('line_number', 'N/A')}")
                print(f"Amount: {item.get('amount', 0):,.2f} THB")
                print(f"Invoice type: {item.get('invoice_type', 'N/A')}")
                
                if item.get('invoice_type') == 'AP':
                    print(f"Agency: {item.get('agency', 'N/A')}")
                    print(f"Project ID: {item.get('project_id', 'N/A')}")
                    print(f"Project Name: {item.get('project_name', 'N/A')}")
                    print(f"Objective: {item.get('objective', 'N/A')}")
                    print(f"Period: {item.get('period', 'N/A')}")
                    print(f"Campaign ID: {item.get('campaign_id', 'N/A')}")
                
                desc = item.get('description', 'N/A')
                if len(desc) > 100:
                    desc = desc[:100] + '...'
                print(f"Description: {desc}")
            
            # Show last 3 items for AP invoices
            if has_ap_fields and len(items) > 5:
                print(f"\n[LAST 3 ITEMS - DETAILED]")
                for i, item in enumerate(items[-3:], len(items)-2):
                    print(f"\n--- Item {i} ---")
                    print(f"Line number: {item.get('line_number', 'N/A')}")
                    print(f"Amount: {item.get('amount', 0):,.2f} THB")
                    print(f"Agency: {item.get('agency', 'N/A')}")
                    print(f"Project ID: {item.get('project_id', 'N/A')}")
                    print(f"Campaign ID: {item.get('campaign_id', 'N/A')}")
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            all_results[platform] = {
                "filename": filename,
                "error": str(e)
            }
    
    # Overall statistics
    print("\n" + "="*100)
    print("OVERALL STATISTICS")
    print("="*100)
    
    total_items = 0
    total_amount = 0
    
    for platform, result in all_results.items():
        if 'error' not in result:
            items = result.get('total_items', 0)
            amount = result.get('total_amount', 0)
            total_items += items
            total_amount += amount
            print(f"\n{platform:20}: {items:4} items, {amount:15,.2f} THB")
    
    print(f"\n{'TOTAL':20}: {total_items:4} items, {total_amount:15,.2f} THB")
    
    # Save detailed JSON report
    report_data = {
        "generated": datetime.now().isoformat(),
        "results": all_results
    }
    
    with open("detailed_test_report.json", "w", encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print("\n[REPORT SAVED] detailed_test_report.json")
    
    # Check for specific issues
    print("\n" + "="*100)
    print("ISSUE ANALYSIS")
    print("="*100)
    
    # Facebook AP analysis
    if "Facebook AP" in all_results and 'items' in all_results["Facebook AP"]:
        fb_ap_items = all_results["Facebook AP"]["items"]
        print(f"\n[Facebook AP Analysis]")
        print(f"Total items: {len(fb_ap_items)}")
        
        # Check for items without project_id
        no_project_id = [item for item in fb_ap_items if item.get('project_id') == 'Unknown']
        print(f"Items without project_id: {len(no_project_id)}")
        
        if no_project_id[:3]:
            print("\nFirst 3 items without project_id:")
            for item in no_project_id[:3]:
                desc = item.get('description', '')[:80]
                print(f"  - {desc}...")
        
        # Check unique project IDs
        project_ids = set(item.get('project_id', 'Unknown') for item in fb_ap_items)
        print(f"\nUnique project IDs found: {len(project_ids)}")
        for pid in sorted(project_ids)[:10]:
            if pid != 'Unknown':
                count = sum(1 for item in fb_ap_items if item.get('project_id') == pid)
                print(f"  - {pid}: {count} items")
    
    return all_results

if __name__ == "__main__":
    generate_detailed_report()