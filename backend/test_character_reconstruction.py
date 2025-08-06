#!/usr/bin/env python3
"""Test character reconstruction on fragmented Google PDFs"""

import sys
import fitz
from google_parser_character_reconstruction import reconstruct_text_from_chars, extract_line_items_from_reconstructed

sys.stdout.reconfigure(encoding='utf-8')

# Test on known fragmented files
test_files = [
    ('5297692778.pdf', 3),   # Should have 3 line items
    ('5297692787.pdf', 8),   # Should have 8 line items
    ('5297692790.pdf', 4),   # Should have 4 line items
    ('5297692799.pdf', 7),   # Should have 7 line items
    ('5298156820.pdf', 11)   # Should have 11 line items
]

for filename, expected_items in test_files:
    print(f"\n{'='*80}")
    print(f"Testing {filename} - Expected {expected_items} items")
    print('='*80)
    
    filepath = f'../Invoice for testing/{filename}'
    invoice_number = filename.replace('.pdf', '')
    
    try:
        with fitz.open(filepath) as doc:
            # Reconstruct text from all pages
            reconstructed_text = ""
            for page in doc:
                reconstructed_text += reconstruct_text_from_chars(page) + "\n"
            
            print("\nSearching for table area...")
            lines = reconstructed_text.split('\n')
            
            # Find table area
            table_start = -1
            table_end = -1
            for i, line in enumerate(lines):
                if 'คำอธิบาย' in line:
                    table_start = i
                    print(f"Found table header at line {i}: {line}")
                elif table_start > -1 and ('ยอดรวม' in line or 'จำนวนเงินรวม' in line):
                    table_end = i
                    print(f"Found table end at line {i}: {line}")
                    break
            
            if table_start > -1:
                print(f"\nTable content (lines {table_start} to {table_end}):")
                print("-" * 40)
                for i in range(max(0, table_start-2), min(len(lines), table_end+2)):
                    if lines[i].strip():
                        print(f"{i:3d}: {lines[i]}")
            
            # Extract line items
            items = extract_line_items_from_reconstructed(reconstructed_text, invoice_number)
            
            print(f"\nExtracted {len(items)} items:")
            print("-" * 40)
            
            total = 0
            for idx, item in enumerate(items, 1):
                print(f"Item {idx}:")
                print(f"  Description: {item['description'][:80]}...")
                print(f"  Amount: {item['amount']:,.2f}")
                total += item['amount']
            
            print(f"\nTotal: {total:,.2f}")
            
            if len(items) == expected_items:
                print("✓ Correct number of items!")
            else:
                print(f"✗ Wrong number of items (expected {expected_items})")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()