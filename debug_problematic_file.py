import fitz
import re
import sys
import io
import os

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append('backend')

def debug_problematic_file(filename):
    """Debug the problematic credit note file"""
    print(f"\n{'='*80}")
    print(f"DEBUGGING PROBLEMATIC FILE: {filename}")
    print('='*80)
    
    filepath = os.path.join("Invoice for testing", filename)
    
    with fitz.open(filepath) as doc:
        full_text = "\n".join(page.get_text() for page in doc)
    
    print(f"File size: {len(full_text)} characters")
    
    # Check for credit note indicators
    credit_indicators = ["credit note", "ใบลดหนี้", "คืนเงิน", "-฿", "นี่เป็นเครดิต", "โปรดอย่าชำระเงิน"]
    found_indicators = []
    
    for indicator in credit_indicators:
        if indicator.lower() in full_text.lower():
            found_indicators.append(indicator)
    
    print(f"Credit indicators found: {found_indicators}")
    
    # Look for negative amounts
    negative_baht = re.findall(r'-฿[\d,]+\.\d{2}', full_text)
    print(f"Negative Baht amounts: {negative_baht}")
    
    # Look for any negative amounts
    negative_amounts = re.findall(r'-\d+[\d,]*\.\d{2}', full_text)
    print(f"Any negative amounts: {negative_amounts}")
    
    # Check for invalid activity text
    invalid_activity_count = full_text.count("กิจกรรมที่ไม่ถูกต้อง")
    print(f"Invalid activity mentions: {invalid_activity_count}")
    
    # Check if this looks like a regular invoice instead of credit note
    google_ads = "Google Ads" in full_text
    google_company = "Google Asia Pacific" in full_text
    invoice_number = re.search(r"(?:Invoice number|หมายเลขใบแจ้งหนี้):\s*([\w-]+)", full_text, re.IGNORECASE)
    
    print(f"Google Ads mention: {google_ads}")
    print(f"Google company: {google_company}")
    print(f"Invoice number: {invoice_number.group(1) if invoice_number else 'Not found'}")
    
    # Show first 500 characters
    print(f"\nFirst 500 characters:")
    print("-" * 40)
    print(full_text[:500])
    
    # Show some lines around the middle
    lines = full_text.split('\n')
    middle = len(lines) // 2
    print(f"\nLines around middle ({middle-5} to {middle+5}):")
    print("-" * 40)
    for i in range(max(0, middle-5), min(len(lines), middle+5)):
        print(f"{i:3d}: {lines[i]}")
    
    # Try to determine why enhanced parser failed
    print(f"\nAnalyzing why enhanced parser might have failed:")
    print("-" * 60)
    
    # Check invoice total extraction
    total_patterns = [
        r'ยอดรวมในสกุลเงิน THB\s*(-?\d+[\d,]*\.\d{2})',
        r'-฿([\d,]+\.\d{2})',
        r'Total.*?(-?\d+[\d,]*\.\d{2})'
    ]
    
    for i, pattern in enumerate(total_patterns):
        matches = re.findall(pattern, full_text)
        print(f"Pattern {i+1} matches: {matches}")

# Debug the problematic file
debug_problematic_file("5302012325.pdf")