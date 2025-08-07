#!/usr/bin/env python3
"""Check specific Facebook invoice that might be the issue"""

import os
import fitz
import sys

sys.stdout.reconfigure(encoding='utf-8')

filename = '246952155.pdf'
filepath = os.path.join('..', 'Invoice for testing', filename)

print("="*80)
print(f"ANALYZING: {filename}")
print("="*80)

with fitz.open(filepath) as doc:
    print(f"Pages: {len(doc)}")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        print(f"\n--- PAGE {page_num + 1} ---")
        lines = text.split('\n')
        
        # Look for key information
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Invoice info
            if 'Invoice' in line and 'Number' in line:
                print(f"Line {i}: {line}")
                if i+1 < len(lines):
                    print(f"Line {i+1}: {lines[i+1].strip()}")
            
            # Total amount
            if 'Total' in line and 'due' in line:
                print(f"Line {i}: {line}")
                if i+1 < len(lines):
                    print(f"Line {i+1}: {lines[i+1].strip()}")
            
            # Amount due
            if 'Amount' in line and 'due' in line:
                print(f"Line {i}: {line}")
                for j in range(1, 4):
                    if i+j < len(lines):
                        print(f"Line {i+j}: {lines[i+j].strip()}")
            
            # Check for ar@meta.com marker
            if 'ar@meta.com' in line:
                print(f"\nFound ar@meta.com at line {i}")
                print("Next 20 lines:")
                for j in range(1, 21):
                    if i+j < len(lines):
                        print(f"  {i+j}: {lines[i+j].strip()}")

# Also check if this is AP or Non-AP
with fitz.open(filepath) as doc:
    text_content = ""
    for page in doc:
        text_content += page.get_text()
    
    has_st_marker = '[ST]' in text_content
    has_pk_pattern = 'pk|' in text_content
    
    print(f"\n[ST] marker found: {has_st_marker}")
    print(f"pk| pattern found: {has_pk_pattern}")
    print(f"Invoice type: {'AP' if (has_st_marker and has_pk_pattern) else 'Non-AP'}")