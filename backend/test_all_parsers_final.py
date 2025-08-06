#!/usr/bin/env python3
"""
Comprehensive test report for all invoice parsers
"""

import os
import fitz
import json
from datetime import datetime

# Import the parsers
from facebook_parser_final_100 import parse_facebook_invoice
from google_parser_extract import parse_google_invoice
from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed

def test_all_parsers():
    """Test all parsers and generate comprehensive report"""
    
    print("="*100)
    print("COMPREHENSIVE INVOICE PARSER TEST REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    invoice_dir = "../Invoice for testing"
    
    # Statistics
    stats = {
        "total_files": 0,
        "processed": 0,
        "errors": 0,
        "by_platform": {
            "Facebook": {"files": 0, "items": 0, "amount": 0, "ap": 0, "non_ap": 0},
            "Google": {"files": 0, "items": 0, "amount": 0, "ap": 0, "non_ap": 0},
            "TikTok": {"files": 0, "items": 0, "amount": 0, "ap": 0, "non_ap": 0},
            "Unknown": {"files": 0, "items": 0, "amount": 0}
        }
    }
    
    # Expected totals for verification
    expected_totals = {
        # Facebook
        "246543739.pdf": 1985559.44,
        "246546622.pdf": 973675.24,
        "246578231.pdf": 94498.17,
        "246649305.pdf": 20198.70,  # Corrected from invoice
        "246727587.pdf": 1066985.58,
        "246738919.pdf": 788488.72,
        "246774670.pdf": 553692.93,
        "246791975.pdf": 1417663.24,
        "246865374.pdf": 506369.23,
        "246952437.pdf": 163374.47,
        # Some Google examples
        "5297692778.pdf": 18482.50,
        "5297692787.pdf": 18875.62,
        "5297692790.pdf": -6284.42,
        # Add more as needed
    }
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(invoice_dir) if f.endswith('.pdf')]
    pdf_files.sort()
    
    stats["total_files"] = len(pdf_files)
    
    # Process each file
    results = {}
    
    for filename in pdf_files:
        filepath = os.path.join(invoice_dir, filename)
        
        try:
            # Read PDF
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            # Determine platform and parse
            if filename.startswith('THTT') or 'TikTok' in text or 'ByteDance' in text:
                platform = "TikTok"
                items = parse_tiktok_invoice_detailed(text, filename)
            elif filename.startswith('5') or ('Google' in text and 'Ads' in text):
                platform = "Google"
                items = parse_google_invoice(text, filename)
            elif filename.startswith('24') or 'Facebook' in text or 'Meta' in text:
                platform = "Facebook"
                items = parse_facebook_invoice(text, filename)
            else:
                platform = "Unknown"
                items = []
            
            # Calculate totals
            total_amount = sum(item.get('amount', 0) for item in items)
            
            # Determine invoice type
            invoice_type = "Unknown"
            if items:
                if any(item.get('invoice_type') == 'AP' for item in items):
                    invoice_type = "AP"
                elif any(item.get('invoice_type') == 'Non-AP' for item in items):
                    invoice_type = "Non-AP"
            
            # Update statistics
            stats["processed"] += 1
            stats["by_platform"][platform]["files"] += 1
            stats["by_platform"][platform]["items"] += len(items)
            stats["by_platform"][platform]["amount"] += total_amount
            
            if invoice_type == "AP":
                stats["by_platform"][platform]["ap"] += 1
            elif invoice_type == "Non-AP":
                stats["by_platform"][platform]["non_ap"] += 1
            
            # Check accuracy if expected total is known
            expected = expected_totals.get(filename)
            accuracy = None
            if expected is not None:
                accuracy = (total_amount / expected * 100) if expected != 0 else 100
            
            # Store results
            results[filename] = {
                "platform": platform,
                "invoice_type": invoice_type,
                "total_items": len(items),
                "total_amount": total_amount,
                "expected_amount": expected,
                "accuracy": accuracy,
                "items": items[:3]  # Store first 3 items as sample
            }
            
        except Exception as e:
            stats["errors"] += 1
            results[filename] = {
                "platform": "Error",
                "error": str(e)
            }
    
    # Print summary
    print("\n" + "="*100)
    print("SUMMARY STATISTICS")
    print("="*100)
    
    print(f"\nTotal files: {stats['total_files']}")
    print(f"Processed: {stats['processed']}")
    print(f"Errors: {stats['errors']}")
    
    print("\nBy Platform:")
    total_amount = 0
    for platform, pstats in stats["by_platform"].items():
        if pstats["files"] > 0:
            print(f"\n{platform}:")
            print(f"  Files: {pstats['files']}")
            print(f"  Total items: {pstats['items']}")
            print(f"  Total amount: {pstats['amount']:,.2f} THB")
            if platform != "Unknown":
                print(f"  AP invoices: {pstats.get('ap', 0)}")
                print(f"  Non-AP invoices: {pstats.get('non_ap', 0)}")
            total_amount += pstats["amount"]
    
    print(f"\nGrand total: {total_amount:,.2f} THB")
    
    # Check accuracy for known files
    print("\n" + "="*100)
    print("ACCURACY VERIFICATION")
    print("="*100)
    
    perfect_count = 0
    checked_count = 0
    
    for filename, expected in expected_totals.items():
        if filename in results:
            result = results[filename]
            if "error" not in result:
                checked_count += 1
                actual = result["total_amount"]
                accuracy = result.get("accuracy", 0)
                
                if accuracy and accuracy >= 99.99:
                    perfect_count += 1
                    status = "PERFECT"
                else:
                    status = f"Diff: {actual - expected:,.2f}"
                
                print(f"\n{filename}:")
                print(f"  Expected: {expected:,.2f}")
                print(f"  Actual: {actual:,.2f}")
                print(f"  Accuracy: {accuracy:.2f}%")
                print(f"  Status: {status}")
    
    print(f"\nPerfect extractions: {perfect_count}/{checked_count}")
    
    # Save detailed JSON report
    report = {
        "generated": datetime.now().isoformat(),
        "statistics": stats,
        "results": results
    }
    
    output_file = "comprehensive_parser_report.json"
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[REPORT SAVED] {output_file}")
    
    return results

if __name__ == "__main__":
    test_all_parsers()