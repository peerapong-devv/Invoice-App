#!/usr/bin/env python3

import re
import os
from PyPDF2 import PdfReader

def analyze_invoice_structure(invoice_number):
    """Analyze the structure of an invoice"""
    
    invoice_dir = "Invoice for testing"
    filename = f"{invoice_number}-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        print(f"Analyzing {invoice_number}")
        print("="*80)
        
        # Find consumption details
        consumption_start = text_content.find('Consumption Details:')
        consumption_text = text_content[consumption_start:]
        
        # Skip the first few lines (headers)
        lines = consumption_text.split('\n')
        
        # Find where the actual data starts (after headers)
        data_start_idx = 0
        for i, line in enumerate(lines):
            if 'THBCash Consumption' in line:
                data_start_idx = i + 2  # Skip the header and next line
                break
        
        print(f"Data starts at line {data_start_idx}")
        print("\nShowing lines from data start:")
        
        # Show the actual data lines
        for i in range(data_start_idx, min(data_start_idx + 30, len(lines))):
            line = lines[i].strip()
            print(f"{i:3}: '{line}'")
        
        # Look for ST patterns in the actual data
        print("\n" + "="*80)
        print("Looking for line items with ST patterns...")
        
        # Pattern to find line items: ST followed by advertiser info
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if re.match(r'^ST\d{10,}', line):
                print(f"\nFound ST at line {i}: {line}")
                # Show next 10 lines
                for j in range(i+1, min(i+11, len(lines))):
                    print(f"  +{j-i}: '{lines[j].strip()}'")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Analyze both AP and non-AP invoices
    test_invoices = [
        "THTT202502215482",  # Non-AP (should have 28,560)
        "THTT202502215575",  # AP (should have 438,111.69)
        "THTT202502216319"   # Non-AP (should have 415,774.47)
    ]
    
    for inv in test_invoices:
        analyze_invoice_structure(inv)
        print("\n" + "="*100 + "\n")