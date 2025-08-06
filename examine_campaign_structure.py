#!/usr/bin/env python3
"""
Examine the structure around the campaign amounts to understand the fragmentation
"""

import fitz
import re

def examine_structure():
    pdf_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\5298528895.pdf"
    
    with fitz.open(pdf_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text()
    
    lines = full_text.split('\n')
    
    print("EXAMINING STRUCTURE AROUND CAMPAIGN AMOUNTS")
    print("=" * 60)
    
    # Find the lines with campaign amounts
    campaign_lines = [193, 301, 408]  # Based on previous output
    
    for line_num in campaign_lines:
        amount = lines[line_num].strip()
        print(f"\nAMOUNT LINE {line_num}: '{amount}'")
        print("Context (20 lines before and 5 after):")
        
        start = max(0, line_num - 20)
        end = min(len(lines), line_num + 6)
        
        for i in range(start, end):
            marker = ">>> " if i == line_num else "    "
            line_content = lines[i].strip()
            
            try:
                print(f"{marker}{i:3d}: '{line_content}'")
            except UnicodeEncodeError:
                safe_content = line_content.encode('ascii', 'ignore').decode('ascii')
                print(f"{marker}{i:3d}: '{safe_content}'")
    
    # Let's also look for the pk pattern reconstruction to see what happened
    print("\n" + "=" * 60)
    print("LOOKING FOR PK RECONSTRUCTION OPPORTUNITY")
    print("=" * 60)
    
    # Check if there are fragmented pk patterns
    for i in range(len(lines) - 2):
        if (lines[i].strip() == 'p' and 
            lines[i+1].strip() == 'k'):
            print(f"\nFound 'p' at line {i}, 'k' at line {i+1}")
            print("Next few lines:")
            for j in range(i, min(len(lines), i + 10)):
                try:
                    print(f"  {j:3d}: '{lines[j].strip()}'")
                except UnicodeEncodeError:
                    safe_content = lines[j].encode('ascii', 'ignore').decode('ascii')
                    print(f"  {j:3d}: '{safe_content.strip()}'")

if __name__ == "__main__":
    examine_structure()