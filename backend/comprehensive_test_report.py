#!/usr/bin/env python3
"""
Comprehensive test report for all invoice parsers
"""

import fitz
import json
from datetime import datetime
from facebook_google_fixed_parsers import parse_facebook_invoice, parse_google_invoice
from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed

def test_all_parsers():
    """Test all parsers and generate comprehensive report"""
    
    print("="*80)
    print("COMPREHENSIVE INVOICE PARSER TEST REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Test data
    test_files = {
        "TikTok AP": "THTT202502215482-Prakit Holdings Public Company Limited-Invoice.pdf",
        "Facebook AP": "246543739.pdf", 
        "Facebook Non-AP": "246617307.pdf",
        "Google Non-AP": "5303655373.pdf"
    }
    
    # Expected totals
    expected_totals = {
        "TikTok AP": 28560.00,  # Actual total from invoice
        "Facebook AP": 1985559.44,
        "Facebook Non-AP": 72621.38,
        "Google Non-AP": 10674.50
    }
    
    results = {}
    
    for test_name, filename in test_files.items():
        print(f"\n{'='*60}")
        print(f"Testing: {test_name}")
        print(f"File: {filename}")
        print("="*60)
        
        try:
            # Read file
            filepath = f"../Invoice for testing/{filename}"
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            # Parse based on platform
            if "TikTok" in test_name:
                items = parse_tiktok_invoice_detailed(text, filename)
            elif "Facebook" in test_name:
                items = parse_facebook_invoice(text, filename)
            elif "Google" in test_name:
                items = parse_google_invoice(text, filename)
            else:
                items = []
            
            # Calculate results
            total_amount = sum(item.get('amount', 0) for item in items)
            expected = expected_totals.get(test_name, 0)
            accuracy = (total_amount / expected * 100) if expected > 0 else 0
            
            # Store results
            results[test_name] = {
                "filename": filename,
                "items_extracted": len(items),
                "total_extracted": total_amount,
                "expected_total": expected,
                "accuracy": accuracy,
                "status": "PASS" if accuracy >= 90 else "FAIL"
            }
            
            # Print summary
            print(f"Items extracted: {len(items)}")
            print(f"Total extracted: {total_amount:,.2f} THB")
            print(f"Expected total: {expected:,.2f} THB")
            print(f"Accuracy: {accuracy:.2f}%")
            print(f"Status: {results[test_name]['status']}")
            
            # Show AP field extraction for AP invoices
            if "AP" in test_name and items:
                print("\nAP Field Extraction Sample (first 3 items):")
                for i, item in enumerate(items[:3], 1):
                    print(f"\n{i}. Item {item.get('line_number', i)}:")
                    print(f"   Amount: {item.get('amount', 0):,.2f}")
                    print(f"   Agency: {item.get('agency', 'N/A')}")
                    print(f"   Project ID: {item.get('project_id', 'N/A')}")
                    print(f"   Project Name: {item.get('project_name', 'N/A')}")
                    print(f"   Objective: {item.get('objective', 'N/A')}")
                    print(f"   Period: {item.get('period', 'N/A')}")
                    print(f"   Campaign ID: {item.get('campaign_id', 'N/A')}")
                
                # Count AP field completeness
                ap_fields = ['agency', 'project_id', 'project_name', 'objective', 'period', 'campaign_id']
                field_counts = {field: 0 for field in ap_fields}
                
                for item in items:
                    for field in ap_fields:
                        if item.get(field) and item.get(field) != 'Unknown':
                            field_counts[field] += 1
                
                print("\nAP Field Completeness:")
                for field, count in field_counts.items():
                    percentage = (count / len(items) * 100) if items else 0
                    print(f"   {field}: {count}/{len(items)} ({percentage:.1f}%)")
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results[test_name] = {
                "filename": filename,
                "error": str(e),
                "status": "ERROR"
            }
    
    # Overall summary
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed = sum(1 for r in results.values() if r.get('status') == 'PASS')
    failed = sum(1 for r in results.values() if r.get('status') == 'FAIL')
    errors = sum(1 for r in results.values() if r.get('status') == 'ERROR')
    
    print(f"\nTotal tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Success rate: {(passed/total_tests*100):.1f}%")
    
    # Save JSON report
    report = {
        "test_date": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": f"{(passed/total_tests*100):.1f}%"
        },
        "results": results
    }
    
    with open("comprehensive_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\nReport saved to: comprehensive_test_report.json")
    
    return results

if __name__ == "__main__":
    test_all_parsers()