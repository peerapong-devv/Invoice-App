#!/usr/bin/env python3
"""
Final validation test for invoice 246791975.pdf
"""
import os
import sys
sys.path.append('backend')

import fitz
from app import process_invoice_file

def validate_246791975():
    """Final validation of invoice 246791975.pdf"""
    
    test_file = "246791975.pdf"
    filepath = os.path.join(r"C:\Users\peerapong\invoice-reader-app\Invoice for testing", test_file)
    
    print("FINAL VALIDATION: 246791975.pdf")
    print("=" * 60)
    
    # Process using backend
    records = process_invoice_file(filepath, test_file)
    
    # Separate AP and Non-AP
    ap_records = [r for r in records if r.get('invoice_type') == 'AP']
    non_ap_records = [r for r in records if r.get('invoice_type') == 'Non-AP']
    
    print(f"Total records: {len(records)}")
    print(f"AP records (with [ST]): {len(ap_records)}")
    print(f"Non-AP records: {len(non_ap_records)}")
    
    # Calculate totals
    ap_total = sum(r['total'] for r in ap_records if r['total'] is not None)
    all_total = sum(r['total'] for r in records if r['total'] is not None)
    
    print(f"\nFinancial Summary:")
    print(f"AP records total: {ap_total:,.2f} THB")
    print(f"All records total: {all_total:,.2f} THB")
    
    # Find the coupon line
    coupon_line = None
    for r in records:
        if 'goodwill' in r.get('description', '').lower() or 'coupon' in r.get('description', '').lower():
            coupon_line = r
            break
    
    if coupon_line:
        print(f"\nCoupon adjustment found:")
        print(f"  Line {coupon_line.get('line_number')}: {coupon_line.get('description')}")
        print(f"  Amount: {coupon_line.get('total'):,.2f} THB")
        print(f"\nInvoice total (1,417,663.24) + Coupon ({coupon_line.get('total'):,.2f}) = {1417663.24 + coupon_line.get('total'):,.2f}")
        print(f"AP records total: {ap_total:,.2f}")
        print(f"Match: {'YES' if abs((1417663.24 + coupon_line.get('total', 0)) - ap_total) < 0.01 else 'NO'}")
    
    # The file was deleted after processing, so we know from previous analysis
    st_count = 119  # Known from our analysis
    print(f"\nVerification:")
    print(f"[ST] markers in PDF (known): {st_count}")
    print(f"AP records extracted: {len(ap_records)}")
    print(f"Match: {'YES' if st_count == len(ap_records) else 'NO'}")
    
    # Show sample records
    print(f"\nSample AP records:")
    for i, record in enumerate(ap_records[:5]):
        print(f"{i+1}. Line {record['line_number']}: Project {record.get('project_id', 'N/A')} | "
              f"Campaign {record.get('campaign_id', 'N/A')} | {record.get('total', 0):,.2f} THB")
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")

if __name__ == "__main__":
    validate_246791975()