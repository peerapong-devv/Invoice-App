#!/usr/bin/env python3

import os
import re
from PyPDF2 import PdfReader

def investigate_concatenation_issue(invoice_number):
    """Investigate why some amounts are missing"""
    
    invoice_dir = "Invoice for testing"
    filename = f"{invoice_number}-Prakit Holdings Public Company Limited-Invoice.pdf"
    file_path = os.path.join(invoice_dir, filename)
    
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            text_content = ''.join([page.extract_text() for page in reader.pages])
        
        print(f"Investigating {invoice_number}")
        print("="*80)
        
        # Find consumption section
        consumption_start = text_content.find('Consumption Details:')
        consumption_text = text_content[consumption_start:]
        
        # Find all lines that contain amounts
        lines = consumption_text.split('\n')
        amount_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*\.\d{2})')
        
        print("Lines containing amounts:")
        print("-"*80)
        
        for i, line in enumerate(lines):
            if amount_pattern.search(line):
                print(f"{i:3}: '{line.strip()}'")
                
                # Check if this line contains concatenated amounts
                amounts = amount_pattern.findall(line)
                if len(amounts) > 1:
                    print(f"     ^ Contains {len(amounts)} amounts: {amounts}")
        
        # Look for lines with ST patterns
        print("\n" + "="*80)
        print("Lines with ST patterns:")
        print("-"*80)
        
        st_pattern = re.compile(r'ST\d{10,}')
        
        for i, line in enumerate(lines):
            if st_pattern.search(line):
                print(f"{i:3}: '{line.strip()}'")
                
                # Show next few lines to see the pattern
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line:
                        print(f"     +{j-i}: '{next_line}'")
                print()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Investigate the problem invoices
    problem_invoices = ["THTT202502215912", "THTT202502215645"]
    
    for inv in problem_invoices:
        investigate_concatenation_issue(inv)
        print("\n" + "="*100 + "\n")