#!/usr/bin/env python3
"""Debug PDF text extraction to see what parser receives"""

import os
import fitz
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Test the problematic file
filepath = os.path.join('..', 'Invoice for testing', '5297692778.pdf')

print("="*80)
print("DEBUG: PDF Text Extraction for 5297692778.pdf")
print("="*80)

with fitz.open(filepath) as doc:
    print(f"Total pages: {len(doc)}")
    
    # Get text using different methods
    print("\n1. Standard get_text():")
    print("-"*40)
    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text()
        full_text += text
        print(f"\nPage {page_num + 1} (first 500 chars):")
        print(repr(text[:500]))
    
    # Check for pk| in various forms
    print("\n2. Checking for pk| patterns:")
    print("-"*40)
    print(f"'pk|' in text: {'pk|' in full_text}")
    print(f"'pk |' in text: {'pk |' in full_text}")
    print(f"'p k |' in text: {'p k |' in full_text}")
    
    # Clean text
    cleaned = full_text.replace('\n', '').replace(' ', '')
    print(f"'pk|' in cleaned text: {'pk|' in cleaned}")
    
    # Find pk pattern with context
    pk_index = full_text.find('p\n')
    if pk_index >= 0:
        print(f"\nFound 'p\\n' at index {pk_index}")
        print(f"Context: {repr(full_text[pk_index:pk_index+50])}")
    
    # Try blocks extraction on page 2
    if len(doc) >= 2:
        print("\n3. Blocks extraction for page 2:")
        print("-"*40)
        page2 = doc[1]
        blocks = page2.get_text("blocks")
        
        for i, block in enumerate(blocks[:10]):
            if len(block) >= 5:
                block_text = block[4]
                if any(char in block_text for char in ['p', 'k', '|', 'P']):
                    print(f"\nBlock {i}: {repr(block_text[:100])}")
    
    # Try dict extraction
    print("\n4. Dict extraction for page 2:")
    print("-"*40)
    if len(doc) >= 2:
        page2 = doc[1]
        dict_data = page2.get_text("dict")
        
        # Reconstruct text preserving layout
        reconstructed = ""
        for block in dict_data["blocks"]:
            if block["type"] == 0:  # Text block
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        line_text += span["text"]
                    reconstructed += line_text + "\n"
        
        # Look for pk patterns
        if 'pk' in reconstructed or 'p\nk' in reconstructed:
            pk_idx = reconstructed.find('p')
            if pk_idx >= 0:
                print(f"Found 'p' at index {pk_idx}")
                print(f"Context:\n{reconstructed[pk_idx:pk_idx+200]}")
        
        # Check for SDH and other AP indicators
        if 'SDH' in reconstructed:
            print("\nFound SDH (AP indicator)")
            sdh_idx = reconstructed.find('SDH')
            print(f"Context:\n{reconstructed[sdh_idx-50:sdh_idx+150]}")