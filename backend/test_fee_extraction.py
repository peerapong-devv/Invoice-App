#!/usr/bin/env python3
"""Test fee extraction from Google invoices"""

import sys
import fitz
from google_parser_character_reconstruction import reconstruct_text_from_chars, clean_fragmented_text

sys.stdout.reconfigure(encoding='utf-8')

# Test file 5297692787 which should have fees
filepath = '../Invoice for testing/5297692787.pdf'

with fitz.open(filepath) as doc:
    # Look for fees on all pages
    for page_num, page in enumerate(doc):
        reconstructed_text = reconstruct_text_from_chars(page)
        reconstructed_text = clean_fragmented_text(reconstructed_text)
        
        lines = reconstructed_text.split('\n')
        
        # Look for fee lines
        for i, line in enumerate(lines):
            if 'ค่าธรรมเนียม' in line or 'fee' in line.lower() or 'regulatory' in line.lower():
                print(f"\nPage {page_num}, Line {i}: {line}")
                # Show context
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    print(f"  {j}: {lines[j]}")
                print("-" * 40)