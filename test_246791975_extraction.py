#!/usr/bin/env python3
"""
Direct test of invoice 246791975.pdf extraction using the backend processing
"""
import os
import sys
sys.path.append('backend')

import fitz  # PyMuPDF

def extract_invoice_246791975():
    """Extract all line items from invoice 246791975.pdf correctly"""
    
    filepath = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\246791975.pdf"
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    print("EXTRACTING INVOICE 246791975.PDF - COMPLETE LINE# ANALYSIS")
    print("=" * 70)
    
    try:
        # Extract text using PyMuPDF
        doc = fitz.open(filepath)
        full_text = "\n".join(page.get_text() for page in doc)
        page_count = doc.page_count
        doc.close()
        
        print(f"Extracted text length: {len(full_text)} characters")
        print(f"Total pages: {page_count}")
        
        # Find all [ST] occurrences
        st_count = full_text.count('[ST]')
        print(f"Total [ST] markers found: {st_count}")
        
        # Split into lines for analysis
        lines = full_text.split('\n')
        print(f"Total lines in document: {len(lines)}")
        
        # Look for Line# patterns
        line_items = []
        current_item = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for Line# pattern
            if line.isdigit() and len(line) <= 3:  # Line numbers
                # Save previous item if exists
                if current_item and 'line_num' in current_item:
                    line_items.append(current_item)
                
                # Start new item
                current_item = {
                    'line_num': int(line),
                    'description': '',
                    'amount': None,
                    'has_st': False
                }
            elif current_item and 'line_num' in current_item:
                # Add to current item description
                if '[ST]' in line:
                    current_item['has_st'] = True
                
                # Check if this line contains amount (ends with number pattern)
                if line.replace(',', '').replace('.', '').replace('-', '').isdigit() or \
                   (line.count('.') == 1 and line.replace('.', '').replace(',', '').replace('-', '').isdigit()):
                    try:
                        # Try to parse as amount
                        amount_str = line.replace(',', '')
                        current_item['amount'] = float(amount_str)
                    except:
                        current_item['description'] += ' ' + line if current_item['description'] else line
                else:
                    current_item['description'] += ' ' + line if current_item['description'] else line
        
        # Add final item
        if current_item and 'line_num' in current_item:
            line_items.append(current_item)
        
        print(f"\nLine items extracted: {len(line_items)}")
        
        # Analysis
        with_st = [item for item in line_items if item['has_st']]
        without_st = [item for item in line_items if not item['has_st']]
        
        print(f"Items with [ST]: {len(with_st)}")
        print(f"Items without [ST]: {len(without_st)}")
        
        # Calculate totals
        total_amount = sum(item['amount'] for item in line_items if item['amount'] is not None)
        st_total = sum(item['amount'] for item in with_st if item['amount'] is not None)
        
        print(f"\nTotal amount: {total_amount:,.2f}")
        print(f"[ST] items total: {st_total:,.2f}")
        
        # Show first 10 items with [ST]
        print(f"\nFIRST 10 ITEMS WITH [ST]:")
        print("-" * 50)
        for item in with_st[:10]:
            desc = item['description'][:60] + ('...' if len(item['description']) > 60 else '')
            print(f"Line {item['line_num']:3d}: {desc}")
            print(f"         Amount: {item['amount']:,.2f} THB")
            print()
        
        # Show items WITHOUT [ST] for verification
        if without_st:
            print(f"\nITEMS WITHOUT [ST] ({len(without_st)} items):")
            print("-" * 50)
            for item in without_st:
                desc = item['description'][:60] + ('...' if len(item['description']) > 60 else '')
                print(f"Line {item['line_num']:3d}: {desc}")
                print(f"         Amount: {item['amount']:,.2f} THB")
        
        return line_items, total_amount, st_count
        
    except Exception as e:
        print(f"Error processing invoice: {e}")
        return None, 0, 0

if __name__ == "__main__":
    extract_invoice_246791975()