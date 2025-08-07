#!/usr/bin/env python3
"""Deep analysis of Google invoice to understand text structure"""

import fitz
import re
import os

def deep_analyze(filename):
    """Deep analysis showing all text and structure"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"DEEP ANALYSIS: {filename}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        # Get text from first page
        page = doc[0]
        text = page.get_text()
        
        # Show raw text with line numbers
        print("\nRAW TEXT (First 100 lines):")
        print("-"*40)
        lines = text.split('\n')
        for i, line in enumerate(lines[:100]):
            if line.strip():
                # Show with ASCII representation for debugging
                ascii_line = line.encode('ascii', 'ignore').decode('ascii')
                if ascii_line != line:
                    print(f"{i:3d}: {repr(line)} -> ASCII: {ascii_line}")
                else:
                    print(f"{i:3d}: {line}")
        
        # Look for patterns
        print("\n\nPATTERN SEARCH:")
        print("-"*40)
        
        # Search for pk patterns (might be fragmented)
        pk_lines = []
        for i, line in enumerate(lines):
            if 'pk' in line or 'p k' in line or 'p\u200bk' in line:
                pk_lines.append((i, line))
        
        print(f"\nLines containing 'pk': {len(pk_lines)}")
        for i, (line_no, line) in enumerate(pk_lines[:5]):
            print(f"  {line_no}: {repr(line)}")
        
        # Search for amounts
        amount_lines = []
        for i, line in enumerate(lines):
            # Look for patterns like numbers with decimals
            if re.search(r'\d+\.\d{2}', line):
                amount_lines.append((i, line))
        
        print(f"\n\nLines with amounts: {len(amount_lines)}")
        for i, (line_no, line) in enumerate(amount_lines[:10]):
            print(f"  {line_no}: {line.strip()}")
        
        # Check for zero-width spaces
        zwsp_count = text.count('\u200b')
        print(f"\n\nZero-width spaces found: {zwsp_count}")
        
        # Check character spans to understand fragmentation
        print("\n\nCHARACTER ANALYSIS (looking for fragmented text):")
        print("-"*40)
        
        # Get character blocks
        blocks = page.get_text("blocks")
        print(f"Total text blocks: {len(blocks)}")
        
        # Show some blocks that might contain pk patterns
        for i, block in enumerate(blocks[:20]):
            block_text = block[4]  # Text is at index 4
            if 'pk' in block_text or any(c in block_text for c in '|0123456789'):
                print(f"\nBlock {i}: {repr(block_text[:100])}")

# Analyze a problematic file
deep_analyze('5297736216.pdf')