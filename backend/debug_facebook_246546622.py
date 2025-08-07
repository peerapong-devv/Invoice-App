#!/usr/bin/env python3
"""Debug Facebook invoice 246546622.pdf"""

import os
import sys
import fitz

sys.stdout.reconfigure(encoding='utf-8')

filepath = os.path.join('..', 'Invoice for testing', '246546622.pdf')

print("="*80)
print("DEBUGGING: 246546622.pdf")
print("Expected total: 974,565.49")
print("Parser total: 973,675.24")
print("Difference: -890.25")
print("="*80)

with fitz.open(filepath) as doc:
    # Find all amounts in the document
    all_amounts = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split('\n')
        
        # Look for ar@meta.com
        ar_meta_line = -1
        for i, line in enumerate(lines):
            if 'ar@meta.com' in line:
                ar_meta_line = i
                print(f"\nPage {page_num + 1}: Found ar@meta.com at line {i}")
                break
        
        if ar_meta_line >= 0:
            # Look for the first few negative amounts
            print("\nLooking for negative amounts after ar@meta.com:")
            for i in range(ar_meta_line + 1, min(ar_meta_line + 15, len(lines))):
                line = lines[i].strip()
                if line.startswith('-') or ('Coupons:' in line):
                    print(f"  Line {i}: {line}")
                    # Check next lines for context
                    for j in range(i+1, min(i+3, len(lines))):
                        if lines[j].strip():
                            print(f"    {j}: {lines[j].strip()}")

# Also check line items structure
print("\n" + "="*80)
print("CHECKING LINE ITEM STRUCTURE")
print("="*80)

with fitz.open(filepath) as doc:
    text = ""
    for page in doc:
        text += page.get_text()
    
    lines = text.split('\n')
    
    # Find ar@meta.com
    ar_idx = -1
    for i, line in enumerate(lines):
        if 'ar@meta.com' in line:
            ar_idx = i
            break
    
    if ar_idx >= 0:
        print(f"ar@meta.com found at line {ar_idx}")
        print("\nFirst 20 lines after ar@meta.com:")
        
        for i in range(ar_idx + 1, min(ar_idx + 21, len(lines))):
            line = lines[i].strip()
            print(f"{i:3d}: {line}")