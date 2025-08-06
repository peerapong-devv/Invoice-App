#!/usr/bin/env python3
"""
Simple analysis of 5298528895.pdf to understand parsing issues
"""

import fitz  # PyMuPDF
import re
import os

def main():
    pdf_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\5298528895.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at {pdf_path}")
        return
    
    print("Analyzing 5298528895.pdf")
    print("=" * 50)
    
    with fitz.open(pdf_path) as doc:
        all_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            all_text += page_text
            print(f"Page {page_num + 1} text length: {len(page_text)}")
    
    # Save to file for analysis
    with open("5298528895_full_text.txt", 'w', encoding='utf-8') as f:
        f.write(all_text)
    
    print(f"Total text length: {len(all_text)}")
    
    # Check for key patterns
    print("\nKey findings:")
    print(f"Contains 'google': {'YES' if 'google' in all_text.lower() else 'NO'}")
    print(f"Contains 'ads': {'YES' if 'ads' in all_text.lower() else 'NO'}")
    print(f"Contains '[ST]': {'YES' if '[ST]' in all_text else 'NO'}")
    print(f"Contains '35,397.74': {'YES' if '35,397.74' in all_text else 'NO'}")
    
    # Count occurrences of the target amount  
    target_count = all_text.count('35,397.74')
    print(f"Number of '35,397.74' occurrences: {target_count}")
    
    # Find all amounts
    amounts = re.findall(r'\d{1,3}(?:,\d{3})*\.\d{2}', all_text)
    print(f"All amounts found: {amounts}")
    
    # Look for line structure
    lines = all_text.split('\n')
    line_numbers = []
    for i, line in enumerate(lines):
        line = line.strip()
        if line.isdigit() and len(line) <= 3:
            line_numbers.append(int(line))
    print(f"Line numbers found: {line_numbers}")
    
    # Check if it should be parsed as Google
    is_google = 'google' in all_text.lower() and 'ads' in all_text.lower()
    print(f"Should be parsed as Google: {'YES' if is_google else 'NO'}")
    
    print("\nText saved to: 5298528895_full_text.txt")

if __name__ == "__main__":
    main()