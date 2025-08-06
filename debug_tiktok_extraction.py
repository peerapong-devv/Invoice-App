#!/usr/bin/env python3

import PyPDF2
import re

def debug_tiktok_text_extraction():
    """Debug the text extraction from TikTok invoice to understand structure"""
    
    # Read the actual PDF
    pdf_path = "Invoice for testing/THTT202502216411-Prakit Holdings Public Company Limited-Invoice.pdf"
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() for page in pdf_reader.pages)
    
    print("FULL TEXT CONTENT:")
    print("=" * 80)
    print(text)
    print("=" * 80)
    
    print("\nLINE BY LINE ANALYSIS:")
    print("=" * 80)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.strip():
            print(f"Line {i:2d}: |{line.strip()}|")
    
    print("\n[ST] PATTERNS FOUND:")
    print("=" * 80)
    st_patterns = re.findall(r'[^|\s]*\[ST\][^|\s]*', text)
    for i, pattern in enumerate(st_patterns):
        print(f"Pattern {i+1}: {pattern}")
    
    print("\nCONSUMPTION DETAILS SECTION:")
    print("=" * 80)
    in_consumption = False
    consumption_lines = []
    
    for line in lines:
        line_clean = line.strip()
        
        if 'Consumption Details:' in line_clean:
            in_consumption = True
            print(f"[START] Found consumption section")
            continue
        
        if in_consumption:
            if 'Subtotal before' in line_clean or 'Total in THB' in line_clean:
                print(f"[END] End of consumption section")
                break
            
            if line_clean:
                consumption_lines.append(line_clean)
                print(f"Consumption line: |{line_clean}|")
    
    print("\nAMOUNTS FOUND:")
    print("=" * 80)
    all_amounts = re.findall(r'[\d,]+\.\d{2}', text)
    for i, amount in enumerate(all_amounts):
        print(f"Amount {i+1}: {amount}")

if __name__ == "__main__":
    debug_tiktok_text_extraction()