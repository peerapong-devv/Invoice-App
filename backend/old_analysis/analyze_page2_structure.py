#!/usr/bin/env python3
"""Analyze page 2 structure in detail"""

import os
import sys
import fitz
import re

sys.stdout.reconfigure(encoding='utf-8')

def analyze_page2(filename):
    """Analyze page 2 structure"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Analyzing Page 2 Structure: {filename}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        if len(doc) < 2:
            print("No page 2 found!")
            return
        
        page2 = doc[1]
        text = page2.get_text()
        
        # Clean text
        text = text.replace('\u200b', '')
        lines = text.split('\n')
        
        # Find table start
        table_start = -1
        for i, line in enumerate(lines):
            if 'คำอธิบาย' in line or 'Description' in line:
                print(f"\nFound table header at line {i}: {line}")
                table_start = i
                break
        
        if table_start < 0:
            print("No table found!")
            return
        
        # Show lines around first campaign
        print(f"\n\nLines {table_start} to {table_start + 100}:")
        print("-" * 40)
        
        for i in range(table_start, min(table_start + 100, len(lines))):
            line = lines[i].strip()
            if line:
                # Check for patterns
                has_pipe = '|' in line
                has_amount = bool(re.search(r'\d+\.\d{2}', line))
                has_dmcrm = 'DMCRM' in line or 'DMC' in line
                
                prefix = f"{i:3d}: "
                if has_pipe:
                    prefix += "[PIPE] "
                if has_amount:
                    prefix += "[AMT] "
                if has_dmcrm:
                    prefix += "[DM] "
                
                print(f"{prefix}{line[:100]}{'...' if len(line) > 100 else ''}")

# Test
analyze_page2('5298156820.pdf')