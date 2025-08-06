#!/usr/bin/env python3
"""
Examine the content of the problematic files to understand their structure
"""

import os
import fitz
import re

def examine_file(filename):
    """Examine a specific file to understand its structure"""
    file_path = os.path.join("Invoice for testing", filename)
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"Examining: {filename}")
    print(f"{'='*60}")
    
    try:
        # Extract text
        with fitz.open(file_path) as doc:
            full_text = "\n".join(page.get_text() for page in doc)
        
        lines = full_text.split('\n')
        
        # Check for keywords
        has_credit_keywords = any(keyword in full_text.lower() for keyword in ["กิจกรรมที่ไม่ถูกต้อง", "credit note", "ใบลดหนี้", "คืนเงิน"])
        has_negative_baht = "-฿" in full_text
        
        print(f"Has credit keywords: {has_credit_keywords}")
        print(f"Has negative baht (-฿): {has_negative_baht}")
        
        # Find all amounts
        positive_amounts = []
        negative_amounts = []
        
        for line in lines:
            line = line.strip()
            # Positive amounts
            if re.match(r'^\d+[\d,]*\.\d{2}$', line):
                try:
                    amount = float(line.replace(',', ''))
                    positive_amounts.append(amount)
                except:
                    pass
            # Negative amounts
            elif re.match(r'^-\d+[\d,]*\.\d{2}$', line):
                try:
                    amount = float(line.replace(',', ''))
                    negative_amounts.append(amount)
                except:
                    pass
        
        print(f"Positive amounts found: {len(positive_amounts)}")
        print(f"Negative amounts found: {len(negative_amounts)}")
        
        if positive_amounts:
            print(f"Positive amounts: {positive_amounts[:10]}...")  # Show first 10
        if negative_amounts:
            print(f"Negative amounts: {negative_amounts}")
        
        # Look for invoice total patterns
        invoice_total_patterns = [
            r'Invoice Total.*?(\d+[\d,]*\.\d{2})',
            r'ยอดรวม.*?(\d+[\d,]*\.\d{2})',
            r'Total.*?(\d+[\d,]*\.\d{2})'
        ]
        
        print("\nLooking for invoice total patterns:")
        for pattern in invoice_total_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                print(f"  Pattern '{pattern}' found: {matches}")
        
        # Look for sections with "กิจกรรมที่ไม่ถูกต้อง"
        print("\nInvalid activity sections:")
        for i, line in enumerate(lines):
            if "กิจกรรมที่ไม่ถูกต้อง" in line:
                print(f"  Line {i}: {line[:100]}...")
                # Show next few lines
                for j in range(1, 5):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        if next_line:
                            print(f"    +{j}: {next_line}")
                        else:
                            break
        
        # Show general structure
        print(f"\nGeneral structure (first 20 non-empty lines):")
        count = 0
        for i, line in enumerate(lines):
            if line.strip() and count < 20:
                print(f"  {i:3d}: {line[:80]}...")
                count += 1
        
        return full_text
        
    except Exception as e:
        print(f"Error examining {filename}: {e}")
        return None

def main():
    """Examine all problematic files"""
    
    problem_files = [
        "5297830454.pdf",  # diff: 1,774 THB
        "5298134610.pdf",  # diff: 1,400 THB
        "5298157309.pdf",  # diff: 1,898 THB  
        "5298361576.pdf"   # diff: 968 THB
    ]
    
    for filename in problem_files:
        examine_file(filename)

if __name__ == "__main__":
    main()