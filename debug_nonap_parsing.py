#!/usr/bin/env python3
"""
Debug Non-AP parsing specifically for 5298528895.pdf
"""

import fitz
import re
import os

def debug_non_ap_parsing():
    """Debug the Non-AP parsing logic in detail"""
    
    pdf_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\5298528895.pdf"
    
    # Extract text
    with fitz.open(pdf_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text()
    
    print("DEBUGGING NON-AP PARSING FOR 5298528895.pdf")
    print("=" * 60)
    
    # This is the pattern used in parse_non_ap_perfect
    amount_pattern = r'^(.+?)\s+([-]?[\d,]+\.\d{2})$'
    
    print(f"Pattern used: {amount_pattern}")
    print("\nSearching for matches...")
    
    matches = re.findall(amount_pattern, full_text, re.MULTILINE)
    
    print(f"Total matches found: {len(matches)}")
    
    for i, (desc, amount_str) in enumerate(matches, 1):
        desc = desc.strip()
        try:
            amount = float(amount_str.replace(',', ''))
        except:
            amount = "PARSE_ERROR"
        
        # Check if this would be skipped
        would_skip = should_skip_line_debug(desc, amount)
        desc_len = len(desc)
        
        try:
            print(f"  {i:2d}: '{desc}' -> {amount}")
        except UnicodeEncodeError:
            safe_desc = desc.encode('ascii', 'ignore').decode('ascii')
            print(f"  {i:2d}: '{safe_desc}' -> {amount}")
        
        print(f"      Length: {desc_len}, Skip: {would_skip}")
        
        if would_skip:
            try:
                print(f"      SKIP REASON: {get_skip_reason(desc, amount)}")
            except UnicodeEncodeError:
                print(f"      SKIP REASON: [Unicode encoding issue]")
        elif desc_len < 5:
            print(f"      SKIP REASON: Description too short")
        else:
            print(f"      WOULD INCLUDE: This would be a valid record")
        print()
    
    # Let's also look at the lines that have amounts to see the structure
    print("\n" + "="*60)
    print("LINES CONTAINING AMOUNTS:")
    print("="*60)
    
    lines = full_text.split('\n')
    for i, line in enumerate(lines):
        if re.search(r'[\d,]+\.\d{2}', line):
            try:
                print(f"Line {i:3d}: '{line.strip()}'")
            except UnicodeEncodeError:
                safe_line = line.encode('ascii', 'ignore').decode('ascii')
                print(f"Line {i:3d}: '{safe_line.strip()}'") 

def should_skip_line_debug(desc: str, amount: float) -> bool:
    """Debug version of should_skip_line_perfect"""
    
    if amount == "PARSE_ERROR":
        return True
    
    skip_keywords = [
        'subtotal', 'total', 'gst', 'vat', 'หน้า', 'page',
        'ครบกำหนด', 'due', 'ยอดรวม', 'จำนวนเงิน', 'amount due',
        'net ', 'invoice number', 'billing', 'balance', 'payment',
        'google asia pacific', 'singapore', 'บริษัท', 'company',
        'address', 'ที่อยู่', 'email', 'phone', 'โทร', 'pasir panjang'
    ]
    
    if any(keyword in desc.lower() for keyword in skip_keywords):
        return True
    
    # Skip pure numbers
    if re.match(r'^[-\d.,\s]+$', desc.strip()):
        return True
    
    # Skip unreasonably large amounts
    if abs(amount) > 1000000:
        return True
    
    return False

def get_skip_reason(desc: str, amount: float) -> str:
    """Get the specific reason why a line would be skipped"""
    
    if amount == "PARSE_ERROR":
        return "Amount parse error"
    
    skip_keywords = [
        'subtotal', 'total', 'gst', 'vat', 'หน้า', 'page',
        'ครบกำหนด', 'due', 'ยอดรวม', 'จำนวนเงิน', 'amount due',
        'net ', 'invoice number', 'billing', 'balance', 'payment',
        'google asia pacific', 'singapore', 'บริษัท', 'company',
        'address', 'ที่อยู่', 'email', 'phone', 'โทร', 'pasir panjang'
    ]
    
    for keyword in skip_keywords:
        if keyword in desc.lower():
            return f"Contains skip keyword: '{keyword}'"
    
    # Skip pure numbers
    if re.match(r'^[-\d.,\s]+$', desc.strip()):
        return "Pure numbers/punctuation"
    
    # Skip unreasonably large amounts
    if abs(amount) > 1000000:
        return "Amount too large"
    
    return "Unknown reason"

if __name__ == "__main__":
    debug_non_ap_parsing()