#!/usr/bin/env python3
"""
Check the pattern of subtotal lines in invoice 246791975.pdf
"""
import os
import fitz

def check_subtotal_patterns():
    filepath = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\246791975.pdf"
    
    doc = fitz.open(filepath)
    full_text = "\n".join(page.get_text() for page in doc)
    doc.close()
    
    lines = full_text.split('\n')
    
    # Find lines with the problematic amount
    subtotal_amount = "1,417,663.24"
    
    print("CHECKING SUBTOTAL PATTERNS")
    print("=" * 60)
    
    for i, line in enumerate(lines):
        if subtotal_amount in line:
            print(f"\nFound at line {i+1}:")
            # Show context (10 lines before and after)
            start = max(0, i-10)
            end = min(len(lines), i+11)
            
            for j in range(start, end):
                marker = ">>>" if j == i else "   "
                print(f"{marker} {j+1:4d}: {lines[j]}")
            
            print("-" * 40)

if __name__ == "__main__":
    check_subtotal_patterns()