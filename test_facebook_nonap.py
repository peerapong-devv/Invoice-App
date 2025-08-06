#!/usr/bin/env python3
"""
Test Facebook Non-AP invoice processing
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('backend')

from app import process_invoice_file

def test_facebook_nonap():
    """Test Facebook Non-AP invoice processing"""
    
    # Test some actual Non-AP invoices that exist
    test_invoices = [
        '246541035.pdf',  # Simple non-AP
        '246571090.pdf',  # Another non-AP
        '246574726.pdf',  # Test extraction
        '247036228.pdf',  # Mixed items
    ]
    
    test_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    print("FACEBOOK NON-AP INVOICE TESTING")
    print("=" * 60)
    
    for invoice_file in test_invoices:
        filepath = os.path.join(test_dir, invoice_file)
        
        if not os.path.exists(filepath):
            print(f"ERROR: File not found: {invoice_file}")
            continue
        
        print(f"\nTesting: {invoice_file}")
        print("-" * 40)
        
        try:
            # Process using backend
            records = process_invoice_file(filepath, invoice_file)
            
            # Analyze results
            non_ap_records = [r for r in records if r.get('invoice_type') == 'Non-AP']
            ap_records = [r for r in records if r.get('invoice_type') == 'AP']
            
            total_amount = sum(r['total'] for r in records if r['total'] is not None)
            
            print(f"Results:")
            print(f"  Total records: {len(records)}")
            print(f"  Non-AP records: {len(non_ap_records)}")
            print(f"  AP records: {len(ap_records)} (should be 0)")
            print(f"  Total amount: {total_amount:,.2f} THB")
            
            # Show sample records
            if non_ap_records:
                print(f"  Sample descriptions:")
                for i, record in enumerate(non_ap_records[:3]):
                    desc = record['description'][:60] + ('...' if len(record['description']) > 60 else '')
                    try:
                        print(f"    Line {record['line_number']}: {desc}")
                        print(f"      Amount: {record['total']:,.2f} THB")
                    except UnicodeEncodeError:
                        print(f"    Line {record['line_number']}: [Unicode description]")
                        print(f"      Amount: {record['total']:,.2f} THB")
            
            # Validation
            if len(ap_records) > 0:
                print(f"  WARNING: Found AP records in Non-AP invoice!")
            if len(non_ap_records) == 0:
                print(f"  ERROR: No Non-AP records found!")
            
        except Exception as e:
            print(f"ERROR processing {invoice_file}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_facebook_nonap()