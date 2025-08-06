#!/usr/bin/env python3

import os
import re
from PyPDF2 import PdfReader

def find_all_amount_lines(invoice_number):
    """Find all amount lines in the invoice to check for missing rows"""
    
    invoice_dir = "Invoice for testing"
    filename = f"{invoice_number}-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        # Find all lines that look like concatenated amounts
        amount_pattern = r'\d{1,3}(?:,\d{3})*\.\d{2}0\.00\d{1,3}(?:,\d{3})*\.\d{2}'
        amount_matches = re.findall(amount_pattern, text_content)
        
        print(f"Found {len(amount_matches)} amount lines in invoice {invoice_number}:")
        print("=" * 80)
        
        total = 0
        for i, match in enumerate(amount_matches, 1):
            # Parse the concatenated amounts
            if '0.00' in match:
                parts = match.split('0.00')
                if len(parts) == 2:
                    try:
                        cash = float(parts[1].replace(',', ''))
                        total += cash
                        print(f"{i:2d}. {match} -> Cash: {cash:>10,.2f}")
                    except:
                        print(f"{i:2d}. {match} -> PARSE ERROR")
        
        print(f"\nTotal from all rows: {total:,.2f}")
        print(f"Expected total: 173,380.83")
        print(f"Difference: {173380.83 - total:,.2f}")
        
        # Check if there are additional patterns we might be missing
        print("\n\nChecking for other amount patterns...")
        
        # Look for amounts that might be on separate lines
        all_amounts = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d{2})', text_content)
        print(f"\nTotal individual amounts found: {len(all_amounts)}")
        
        # Group amounts by value to find patterns
        amount_counts = {}
        for amt in all_amounts:
            try:
                value = float(amt.replace(',', ''))
                if value > 0 and value < 100000:  # Reasonable range for line items
                    amount_counts[value] = amount_counts.get(value, 0) + 1
            except:
                pass
        
        print("\nFrequent amounts (appearing 2+ times):")
        for value, count in sorted(amount_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 2:
                print(f"  {value:>10,.2f} appears {count} times")
        
    except Exception as e:
        print(f"Error: {e}")

# Check the problematic invoices
if __name__ == "__main__":
    print("ANALYZING INVOICE THTT202502215912")
    print("=" * 80)
    find_all_amount_lines("THTT202502215912")
    
    print("\n\nANALYZING INVOICE THTT202502215955")  
    print("=" * 80)
    find_all_amount_lines("THTT202502215955")