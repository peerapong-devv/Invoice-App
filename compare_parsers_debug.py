#!/usr/bin/env python3

import os
import sys
from PyPDF2 import PdfReader

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from final_tiktok_parser import parse_tiktok_invoice_final
from working_tiktok_parser_lookup import parse_tiktok_invoice_lookup

def compare_parsers():
    """Compare the results of both parsers to find missing amounts"""
    
    invoice_dir = "Invoice for testing"
    if not os.path.exists(invoice_dir):
        print(f"Error: Directory '{invoice_dir}' not found")
        return
    
    # Get all TikTok files
    tiktok_files = [f for f in os.listdir(invoice_dir) if f.startswith('THTT') and f.endswith('.pdf')]
    tiktok_files.sort()
    
    print(f"Found {len(tiktok_files)} TikTok invoice files")
    print("=" * 80)
    
    # Track totals
    lookup_total = 0
    current_total = 0
    missing_invoices = []
    incorrect_amounts = []
    
    # Process each file
    for filename in tiktok_files:
        file_path = os.path.join(invoice_dir, filename)
        invoice_number = filename.replace('-Prakit Holdings Public Company Limited-Invoice.pdf', '')
        
        try:
            # Read PDF
            with open(file_path, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                text_content = ''.join([page.extract_text() for page in reader.pages])
            
            # Parse with lookup parser
            lookup_records = parse_tiktok_invoice_lookup(text_content, filename)
            lookup_amount = lookup_records[0]['amount'] if lookup_records else 0
            lookup_total += lookup_amount
            
            # Parse with current parser
            current_records = parse_tiktok_invoice_final(text_content, filename)
            current_amount = sum(r['total'] for r in current_records if r['total'])
            current_total += current_amount
            
            # Compare results
            if lookup_amount > 0 and current_amount == 0:
                missing_invoices.append({
                    'invoice': invoice_number,
                    'expected': lookup_amount,
                    'actual': 0,
                    'difference': lookup_amount
                })
                print(f"MISSING: {invoice_number} - Expected: {lookup_amount:,.2f}, Got: 0")
            elif abs(lookup_amount - current_amount) > 0.01:
                incorrect_amounts.append({
                    'invoice': invoice_number,
                    'expected': lookup_amount,
                    'actual': current_amount,
                    'difference': lookup_amount - current_amount
                })
                print(f"INCORRECT: {invoice_number} - Expected: {lookup_amount:,.2f}, Got: {current_amount:,.2f}, Diff: {lookup_amount - current_amount:,.2f}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"Lookup Parser Total: {lookup_total:,.2f} THB")
    print(f"Current Parser Total: {current_total:,.2f} THB")
    print(f"Total Difference: {lookup_total - current_total:,.2f} THB")
    print(f"Expected Total: 2,440,716.88 THB")
    
    print("\n" + "=" * 80)
    print(f"Missing Invoices ({len(missing_invoices)} files):")
    for inv in missing_invoices:
        print(f"  {inv['invoice']}: {inv['expected']:,.2f} THB")
    
    print(f"\nIncorrect Amounts ({len(incorrect_amounts)} files):")
    for inv in incorrect_amounts:
        print(f"  {inv['invoice']}: Expected {inv['expected']:,.2f}, Got {inv['actual']:,.2f}, Diff: {inv['difference']:,.2f}")
    
    # Calculate missing amount breakdown
    missing_from_not_parsed = sum(inv['difference'] for inv in missing_invoices)
    missing_from_incorrect = sum(inv['difference'] for inv in incorrect_amounts)
    
    print(f"\nMissing Amount Breakdown:")
    print(f"  From unparsed invoices: {missing_from_not_parsed:,.2f} THB")
    print(f"  From incorrect amounts: {missing_from_incorrect:,.2f} THB")
    print(f"  Total missing: {missing_from_not_parsed + missing_from_incorrect:,.2f} THB")

if __name__ == "__main__":
    compare_parsers()