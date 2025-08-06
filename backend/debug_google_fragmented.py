#!/usr/bin/env python3
"""Debug Google fragmented text reconstruction"""

import fitz
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Test on file 5297692778 which should have 3 items
filepath = '../Invoice for testing/5297692778.pdf'

with fitz.open(filepath) as doc:
    text = ''
    for page in doc:
        text += page.get_text()

lines = text.split('\n')

# Find table area
table_start = -1
for i, line in enumerate(lines):
    if 'คำอธิบาย' in line:
        table_start = i
        print(f"Table starts at line {i}")
        break

if table_start > -1:
    # Process table area looking for patterns
    i = table_start + 3
    pattern_count = 0
    
    while i < len(lines) and i < table_start + 300:  # Look at next 300 lines
        line = lines[i].strip()
        
        # Check for amounts
        if re.match(r'^\d{1,3}(?:,\d{3})*\.\d{2}$', line):
            print(f"\nFound amount at line {i}: {line}")
            
            # Look back for pattern
            pattern_parts = []
            for j in range(max(0, i - 100), i):
                test_line = lines[j].strip()
                # Remove zero-width spaces
                clean = test_line.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
                if len(clean) == 1 and clean not in ['', ' ', '\t', '\n']:
                    pattern_parts.append(clean)
                elif pattern_parts and test_line:
                    # End of single char sequence
                    if len(pattern_parts) > 10:  # Likely a pattern
                        reconstructed = ''.join(pattern_parts)
                        if 'pk|' in reconstructed or reconstructed.startswith('pk'):
                            print(f"  Reconstructed pattern: {reconstructed[:80]}...")
                            pattern_count += 1
                    pattern_parts = []
        
        i += 1

print(f"\nTotal patterns found: {pattern_count}")