#!/usr/bin/env python3
"""Check 5297692778.pdf in detail for AP patterns"""

import os
import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

filepath = os.path.join('..', 'Invoice for testing', '5297692778.pdf')

print("="*80)
print("DETAILED CHECK: 5297692778.pdf")
print("="*80)

with fitz.open(filepath) as doc:
    print(f"Total pages: {len(doc)}")
    
    # Check each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        print(f"\n--- PAGE {page_num + 1} ---")
        print(f"Text length: {len(text)} characters")
        
        # Check for AP indicators
        ap_patterns = [
            'pk|', 'pk |', 'pk|', 'pk \\|',  # Different pk patterns
            '2089P', '2159P', '2218P',  # Campaign IDs
            'DMCRM', 'DMHEALTH', 'SDH',  # Project codes
            'Traffic', 'Awareness', 'Conversion'  # Objectives
        ]
        
        for pattern in ap_patterns:
            if pattern in text:
                print(f"  ✓ Found '{pattern}'")
                # Find all occurrences
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if pattern in line:
                        print(f"    Line {i}: {line.strip()[:100]}...")
        
        # Look for pipe characters specifically
        if '|' in text:
            print("\n  Found pipe '|' characters:")
            lines = text.split('\n')
            pipe_count = 0
            for i, line in enumerate(lines):
                if '|' in line and pipe_count < 10:  # Show first 10
                    print(f"    Line {i}: {line.strip()[:100]}...")
                    pipe_count += 1
                    
                    # Check context around pipe
                    if 'pk' in line.lower():
                        print(f"      >>> POTENTIAL pk| PATTERN!")
                        # Show next few lines
                        for j in range(1, 4):
                            if i + j < len(lines):
                                print(f"      +{j}: {lines[i+j].strip()[:80]}...")
        
        # Extract text blocks to see structure
        if page_num == 1:  # Focus on page 2
            print("\n  Checking page 2 structure:")
            blocks = page.get_text("blocks")
            
            print(f"  Total blocks: {len(blocks)}")
            
            # Look for blocks with pk or |
            for idx, block in enumerate(blocks):
                if len(block) >= 5:  # Valid text block
                    block_text = block[4]
                    if ('pk' in block_text.lower() or '|' in block_text) and idx < 20:
                        print(f"\n  Block {idx}: {block_text.strip()[:150]}...")
        
        # Try different extraction methods
        if page_num == 1:
            print("\n  Trying different text extraction methods:")
            
            # Method 1: Dict extraction
            dict_text = page.get_text("dict")
            all_text = ""
            for block in dict_text["blocks"]:
                if block["type"] == 0:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            all_text += span["text"] + " "
            
            if 'pk' in all_text.lower() and '|' in all_text:
                print("  ✓ Found pk and | in dict extraction")
                # Find the pattern
                pk_matches = re.findall(r'pk[^a-zA-Z]{0,3}\|[^\n]+', all_text, re.IGNORECASE)
                if pk_matches:
                    print("  Found pk| patterns:")
                    for match in pk_matches[:5]:
                        print(f"    {match[:100]}...")

# Also check raw bytes
print("\n" + "="*80)
print("CHECKING RAW TEXT PATTERNS")
print("="*80)

with fitz.open(filepath) as doc:
    if len(doc) >= 2:
        page2 = doc[1]
        text = page2.get_text()
        
        # Look for fragmented pk| pattern
        lines = text.split('\n')
        for i in range(len(lines) - 1):
            line = lines[i].strip()
            next_line = lines[i+1].strip() if i+1 < len(lines) else ""
            
            # Check if pk is on one line and | on next
            if line.endswith('pk') and next_line.startswith('|'):
                print(f"Found fragmented pk| at lines {i}-{i+1}:")
                print(f"  {line}")
                print(f"  {next_line}")
            
            # Check for various pk patterns
            if re.search(r'pk\s*[|｜]', line, re.IGNORECASE):
                print(f"Found pk pattern at line {i}: {line[:100]}...")