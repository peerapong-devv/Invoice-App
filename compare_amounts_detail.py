#!/usr/bin/env python3

import os
import sys
from PyPDF2 import PdfReader

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fixed_tiktok_concatenation_parser import parse_tiktok_invoice_fixed
from working_tiktok_parser_lookup import parse_tiktok_invoice_lookup

def compare_invoice_amounts():
    """Compare parsed amounts with lookup table"""
    
    invoice_dir = "Invoice for testing"
    
    # Lookup table from user
    expected_amounts = {
        'THTT202502215482': 28560, 'THTT202502215496': 32644.19, 'THTT202502215532': 2000,
        'THTT202502215554': 36324.39, 'THTT202502215575': 438111.69, 'THTT202502215645': 357261.56,
        'THTT202502215678': 103078.96, 'THTT202502215759': 2400, 'THTT202502215819': 9999.73,
        'THTT202502215864': 106391.3, 'THTT202502215912': 173380.83, 'THTT202502215950': 41857.38,
        'THTT202502215955': 178218.52, 'THTT202502216210': 272794.74, 'THTT202502216319': 415774.47,
        'THTT202502216315': 80000, 'THTT202502216411': 8323.05, 'THTT202502216526': 6420.97,
        'THTT202502216580': 48986.8, 'THTT202502216572': 81992.6, 'THTT202502216594': 14696.01,
        'THTT202502216602': 1499.69
    }
    
    tiktok_files = [f for f in os.listdir(invoice_dir) if f.startswith('THTT') and f.endswith('.pdf')]
    tiktok_files.sort()
    
    print("Invoice Number         Expected      Parsed      Difference   Status")
    print("="*70)
    
    total_expected = 0
    total_parsed = 0
    incorrect_invoices = []
    
    for filename in tiktok_files:
        file_path = os.path.join(invoice_dir, filename)
        invoice_number = filename.replace('-Prakit Holdings Public Company Limited-Invoice.pdf', '')
        
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                text_content = ''.join([page.extract_text() for page in reader.pages])
            
            # Get expected amount
            expected = expected_amounts.get(invoice_number, 0)
            total_expected += expected
            
            # Parse with fixed parser
            records = parse_tiktok_invoice_fixed(text_content, filename)
            parsed = sum(r['total'] for r in records if r['total'])
            total_parsed += parsed
            
            # Compare
            diff = expected - parsed
            status = "OK" if abs(diff) < 0.01 else "WRONG"
            
            if status == "WRONG":
                incorrect_invoices.append({
                    'invoice': invoice_number,
                    'expected': expected,
                    'parsed': parsed,
                    'difference': diff
                })
            
            print(f"{invoice_number:<20} {expected:>10,.2f} {parsed:>10,.2f} {diff:>12,.2f}   {status}")
            
        except Exception as e:
            print(f"{invoice_number:<20} Error: {e}")
    
    print("="*70)
    print(f"{'TOTAL':<20} {total_expected:>10,.2f} {total_parsed:>10,.2f} {total_expected - total_parsed:>12,.2f}")
    
    if incorrect_invoices:
        print("\n" + "="*70)
        print("INCORRECT INVOICES:")
        print("="*70)
        for inv in incorrect_invoices:
            print(f"\n{inv['invoice']}:")
            print(f"  Expected: {inv['expected']:,.2f} THB")
            print(f"  Parsed:   {inv['parsed']:,.2f} THB")
            print(f"  Missing:  {inv['difference']:,.2f} THB")

if __name__ == "__main__":
    compare_invoice_amounts()