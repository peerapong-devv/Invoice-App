#!/usr/bin/env python3
"""
Raw Text Analyzer - Examine exact text content to understand Google invoice structure
"""

import fitz
import json
import re

def analyze_raw_text(pdf_path: str, filename: str):
    """Analyze raw text content of PDF"""
    
    print(f"\n{'='*80}")
    print(f"RAW TEXT ANALYSIS: {filename}")
    print(f"{'='*80}")
    
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"\n--- PAGE {page_num + 1} ---")
        
        # Get raw text
        text = page.get_text()
        
        # Get text with layout
        text_dict = page.get_text("dict")
        
        print(f"Raw text length: {len(text)}")
        print("\nFirst 1000 characters:")
        print("-" * 50)
        try:
            # Try to print with ASCII encoding
            ascii_text = text[:1000].encode('ascii', 'ignore').decode('ascii')
            print(f"ASCII version: {repr(ascii_text)}")
        except:
            print("[Contains non-ASCII characters - cannot display]")
        
        # Save raw text to file for inspection
        with open(f"raw_text_{filename}_{page_num+1}.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Raw text saved to: raw_text_{filename}_{page_num+1}.txt")
        print("-" * 50)
        
        # Look for amounts
        amounts = re.findall(r'(-?\d{1,3}(?:,\d{3})*\.?\d{0,2})', text)
        print(f"\nFound {len(amounts)} potential amounts:")
        for i, amount in enumerate(amounts[:20], 1):  # Show first 20
            try:
                val = float(amount.replace(',', ''))
                if abs(val) >= 10:  # Only significant amounts
                    print(f"  {i}. {amount} ({val})")
            except:
                pass
        
        # Look for specific patterns
        print(f"\nLooking for key patterns:")
        
        # Campaign patterns
        pk_matches = re.findall(r'pk\|[^|]*\|[^|]*', text)
        print(f"pk| patterns: {len(pk_matches)}")
        for match in pk_matches[:5]:
            print(f"  - {match[:100]}...")
        
        # Credit patterns
        credit_matches = re.findall(r'กิจกรรมที่ไม่ถูกต้อง[^0-9]*(-?\d{1,3}(?:,\d{3})*\.?\d{2})', text)
        print(f"Credit adjustments: {len(credit_matches)}")
        for match in credit_matches:
            print(f"  - {match}")
        
        # Project descriptions
        project_matches = re.findall(r'[A-Z][a-zA-Z\s\-_]{10,50}', text)
        print(f"Potential project names: {len(project_matches)}")
        for match in project_matches[:10]:
            if not re.match(r'^[A-Z\s]+$', match):  # Skip all-caps words
                print(f"  - {match}")
        
        print(f"\n--- DETAILED BLOCK ANALYSIS ---")
        
        # Analyze blocks in detail
        for i, block in enumerate(text_dict.get("blocks", [])):
            if block.get("type") == 0:  # Text block
                block_text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text += span.get("text", "")
                
                if len(block_text) > 50:  # Only significant blocks
                    print(f"\nBlock {i}: {len(block_text)} chars")
                    try:
                        ascii_preview = block_text[:200].encode('ascii', 'ignore').decode('ascii')
                        print(f"Preview: {repr(ascii_preview)}")
                    except:
                        print(f"Preview: [Non-ASCII content - {len(block_text)} chars]")
                    
                    # Check if this block contains line items
                    amounts_in_block = re.findall(r'(-?\d{1,3}(?:,\d{3})*\.?\d{2})', block_text)
                    if amounts_in_block:
                        print(f"Amounts in this block: {amounts_in_block}")
    
    doc.close()

def analyze_all_problematic():
    """Analyze all problematic invoices"""
    
    base_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    files = ["5297692778.pdf", "5297692787.pdf", "5300624442.pdf"]
    
    for filename in files:
        pdf_path = f"{base_path}\\{filename}"
        analyze_raw_text(pdf_path, filename)

if __name__ == "__main__":
    analyze_all_problematic()