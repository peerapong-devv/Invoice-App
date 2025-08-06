#!/usr/bin/env python3
"""
Test the integrated parser with the fixed 5298528895.pdf
"""

import fitz
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_integrated_parser():
    """Test the integrated parser"""
    
    pdf_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\5298528895.pdf"
    
    # Extract text
    with fitz.open(pdf_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text()
    
    print("TESTING INTEGRATED PARSER WITH 5298528895.pdf")
    print("=" * 60)
    
    # Import the main app process_invoice_file function
    from app import process_invoice_file
    
    try:
        # Test with the actual file
        records = process_invoice_file(pdf_path, "5298528895.pdf")
        
        print(f"Records generated: {len(records)}")
        
        for i, record in enumerate(records, 1):
            print(f"  Record {i}:")
            print(f"    Platform: {record.get('platform')}")
            print(f"    Invoice Type: {record.get('invoice_type')}")
            print(f"    Item Type: {record.get('item_type')}")
            print(f"    Total: {record.get('total')}")
            print(f"    Invoice Total: {record.get('invoice_total')}")
            print(f"    Description: {record.get('description', '')[:50]}...")
            print()
        
        # Check if the total is correctly extracted
        invoice_totals = [r.get('invoice_total') for r in records if r.get('invoice_total')]
        if invoice_totals:
            print(f"✓ SUCCESS: Invoice total extracted as: {invoice_totals[0]}")
            if invoice_totals[0] == 35397.74:
                print("✓ PERFECT: Extracted total matches expected 35,397.74 THB")
            else:
                print(f"⚠ WARNING: Expected 35,397.74 but got {invoice_totals[0]}")
        else:
            print("✗ FAILED: No invoice total extracted")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integrated_parser()