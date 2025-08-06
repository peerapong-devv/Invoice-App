#!/usr/bin/env python3
"""
Debug Google PDF text extraction to understand why patterns aren't being detected
"""

import os
import re
import PyPDF2

def debug_pdf_extraction(filename: str):
    """Debug the PDF extraction for a specific file"""
    
    pdf_path = os.path.join(r"C:\Users\peerapong\invoice-reader-app\Invoice for testing", filename)
    
    print(f"=== DEBUGGING {filename} ===")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"Number of pages: {len(reader.pages)}")
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                print(f"\n--- PAGE {page_num + 1} ---")
                print(f"Text length: {len(text)} characters")
                
                # Show first 500 characters
                print("First 500 characters:")
                print(repr(text[:500]))
                print()
                
                # Check for key patterns
                print("Pattern checks:")
                print(f"  Contains 'pk|': {'YES' if 'pk|' in text else 'NO'}")
                print(f"  Contains 'หมายเลขใบแจ้งหนี้': {'YES' if 'หมายเลขใบแจ้งหนี้' in text else 'NO'}")
                print(f"  Contains 'THB': {'YES' if 'THB' in text else 'NO'}")
                print(f"  Contains 'การคลิก': {'YES' if 'การคลิก' in text else 'NO'}")
                
                # Look for invoice ID
                invoice_match = re.search(r'หมายเลขใบแจ้งหนี้:\s*(\d+)', text)
                if invoice_match:
                    print(f"  Invoice ID found: {invoice_match.group(1)}")
                else:
                    print("  Invoice ID: NOT FOUND")
                
                # Look for total amount
                total_patterns = [
                    r'จำนวนเงินรวมที่ต้องชำระในสกุลเงิน\s+THB\s*฿?([-\d,]+\.?\d*)',
                    r'ยอดรวมในสกุลเงิน\s+THB\s*฿?([-\d,]+\.?\d*)',
                ]
                
                for pattern in total_patterns:
                    total_match = re.search(pattern, text)
                    if total_match:
                        print(f"  Total amount found: {total_match.group(1)}")
                        break
                else:
                    print("  Total amount: NOT FOUND")
                
                # Look for pk| patterns
                pk_patterns = re.findall(r'pk\|[^\s]+', text)
                print(f"  PK patterns found: {len(pk_patterns)}")
                for i, pk in enumerate(pk_patterns[:3]):  # Show first 3
                    print(f"    {i+1}: {pk}")
                
                print()
    
    except Exception as e:
        print(f"Error processing {filename}: {e}")

def test_multiple_files():
    """Test multiple files to see patterns"""
    
    test_files = [
        "5297692778.pdf",  # Should have AP data
        "5297692787.pdf",  # Should have AP data  
        "5297692790.pdf",  # Should have Non-AP data
        "5298248238.pdf",  # Another file
    ]
    
    for filename in test_files:
        debug_pdf_extraction(filename)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_multiple_files()