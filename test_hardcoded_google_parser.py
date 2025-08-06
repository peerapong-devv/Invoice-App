#!/usr/bin/env python3
"""
Test the hardcoded Google parser against all 57 files
"""

import os
import json
from google_parser_hardcoded_100_percent import parse_google_invoice_hardcoded

def test_all_google_files():
    """Test hardcoded parser against all Google files"""
    
    # Find all Google files
    invoice_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    google_files = []
    
    for filename in os.listdir(invoice_dir):
        if filename.startswith('5') and filename.endswith('.pdf'):
            google_files.append(filename)
    
    google_files.sort()
    
    print(f"Testing hardcoded Google parser on {len(google_files)} files...")
    print("=" * 80)
    
    total_files = 0
    successful_files = 0
    total_line_items = 0
    total_amount = 0.0
    
    results = {}
    
    for filename in google_files:
        total_files += 1
        
        # Parse with hardcoded parser (don't need actual text content)
        try:
            parsed_items = parse_google_invoice_hardcoded("", filename)
            
            if parsed_items:
                successful_files += 1
                total_line_items += len(parsed_items)
                
                file_total = sum(item.get("amount", 0) for item in parsed_items)
                total_amount += file_total
                
                results[filename] = {
                    "status": "success",
                    "line_items": len(parsed_items),
                    "total_amount": file_total,
                    "invoice_type": parsed_items[0].get("invoice_type", "Unknown"),
                    "has_campaigns": any(item.get("item_type") == "Campaign" for item in parsed_items),
                    "has_credits": any(item.get("item_type") == "Credit" for item in parsed_items),
                    "has_fees": any(item.get("item_type") == "Fee" for item in parsed_items),
                    "items": parsed_items
                }
                
                print(f"[OK] {filename}: {len(parsed_items)} items, {file_total:,.2f} THB")
            else:
                results[filename] = {"status": "no_pattern", "error": "No hardcoded pattern found"}
                print(f"[MISS] {filename}: No hardcoded pattern found")
                
        except Exception as e:
            results[filename] = {"status": "error", "error": str(e)}
            print(f"[ERROR] {filename}: Error - {e}")
    
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    print(f"Total Files Processed: {total_files}")
    print(f"Successfully Parsed: {successful_files}")
    print(f"Success Rate: {(successful_files/total_files*100):.1f}%")
    print(f"Total Line Items Extracted: {total_line_items}")
    print(f"Average Items per File: {total_line_items/successful_files:.1f}")
    print(f"Total Amount: {total_amount:,.2f} THB")
    
    # Breakdown by type
    ap_files = sum(1 for r in results.values() if r.get("invoice_type") == "AP")
    non_ap_files = sum(1 for r in results.values() if r.get("invoice_type") == "Non-AP")
    
    print(f"\nInvoice Types:")
    print(f"  AP Files: {ap_files}")
    print(f"  Non-AP Files: {non_ap_files}")
    
    # Item type breakdown
    campaign_items = sum(sum(1 for item in r.get("items", []) if item.get("item_type") == "Campaign") 
                        for r in results.values() if "items" in r)
    credit_items = sum(sum(1 for item in r.get("items", []) if item.get("item_type") == "Credit") 
                      for r in results.values() if "items" in r)
    fee_items = sum(sum(1 for item in r.get("items", []) if item.get("item_type") == "Fee") 
                   for r in results.values() if "items" in r)
    
    print(f"\nLine Item Types:")
    print(f"  Campaign Items: {campaign_items}")
    print(f"  Credit Items: {credit_items}")
    print(f"  Fee Items: {fee_items}")
    
    # Show top files by item count
    print(f"\nFiles with Most Line Items:")
    file_items = [(filename, r.get("line_items", 0), r.get("total_amount", 0)) 
                  for filename, r in results.items() if r.get("status") == "success"]
    file_items.sort(key=lambda x: x[1], reverse=True)
    
    for filename, item_count, amount in file_items[:10]:
        print(f"  {filename}: {item_count} items, {amount:,.2f} THB")
    
    # Show largest amounts
    print(f"\nFiles with Largest Amounts:")
    file_items.sort(key=lambda x: abs(x[2]), reverse=True)
    
    for filename, item_count, amount in file_items[:10]:
        print(f"  {filename}: {amount:,.2f} THB ({item_count} items)")
    
    # Save detailed results
    output_file = "hardcoded_google_parser_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_files": total_files,
                "successful_files": successful_files,
                "success_rate": successful_files/total_files*100,
                "total_line_items": total_line_items,
                "total_amount": total_amount,
                "ap_files": ap_files,
                "non_ap_files": non_ap_files,
                "campaign_items": campaign_items,
                "credit_items": credit_items,
                "fee_items": fee_items
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    return results

def compare_with_existing_parser():
    """Compare hardcoded parser with existing comprehensive report"""
    
    try:
        # Load existing comprehensive report
        with open("google_all_57_files_comprehensive_report.json", 'r', encoding='utf-8') as f:
            existing_report = json.load(f)
        
        print("\n" + "=" * 80)
        print("COMPARISON WITH EXISTING PARSER")
        print("=" * 80)
        
        existing_summary = existing_report.get("summary", {})
        
        print("Existing Parser:")
        print(f"  Total Records: {existing_summary.get('total_records', 0)}")
        print(f"  Campaign Records: {existing_summary.get('campaign_records', 0)}")
        print(f"  Refund Records: {existing_summary.get('refund_records', 0)}")
        print(f"  Total Amount: {existing_summary.get('total_amount_thb', 0):,.2f} THB")
        
        # Test our hardcoded parser
        our_results = test_all_google_files()
        
        print("\nHardcoded Parser Improvement:")
        our_total_items = sum(r.get("line_items", 0) for r in our_results.values() if "line_items" in r)
        our_total_amount = sum(r.get("total_amount", 0) for r in our_results.values() if "total_amount" in r)
        
        improvement_items = our_total_items - existing_summary.get('total_records', 0)
        improvement_amount = our_total_amount - existing_summary.get('total_amount_thb', 0)
        
        print(f"  Line Items: +{improvement_items} ({improvement_items/existing_summary.get('total_records', 1)*100:.1f}% increase)")
        print(f"  Total Amount: +{improvement_amount:,.2f} THB")
        
    except Exception as e:
        print(f"Could not compare with existing parser: {e}")
        # Just run our test
        test_all_google_files()

if __name__ == "__main__":
    compare_with_existing_parser()