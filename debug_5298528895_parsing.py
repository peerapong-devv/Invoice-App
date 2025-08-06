#!/usr/bin/env python3
"""
Debug specific parsing issues with 5298528895.pdf
"""

import fitz
import re
from collections import Counter
import sys
import os

# Add the backend directory to the path so we can import the parser
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def debug_google_parser():
    """Debug the Google parser with the specific file"""
    
    pdf_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\5298528895.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at {pdf_path}")
        return
    
    # Extract text
    with fitz.open(pdf_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text()
    
    print("DEBUGGING 5298528895.pdf")
    print("=" * 60)
    
    # Debug the platform detection first
    print("\n1. PLATFORM DETECTION:")
    is_google = 'google' in full_text.lower() and 'ads' in full_text.lower()
    print(f"   Contains 'google': {'YES' if 'google' in full_text.lower() else 'NO'}")
    print(f"   Contains 'ads': {'YES' if 'ads' in full_text.lower() else 'NO'}")
    print(f"   Should parse as Google: {'YES' if is_google else 'NO'}")
    
    # Debug the invoice total extraction
    print("\n2. INVOICE TOTAL EXTRACTION:")
    debug_extract_invoice_total(full_text)
    
    # Debug AP vs Non-AP detection
    print("\n3. AP vs NON-AP DETECTION:")
    debug_ap_detection(full_text)
    
    # Try running the actual parser
    print("\n4. ACTUAL PARSER RESULTS:")
    try:
        from perfect_google_parser import parse_google_invoice_perfect, validate_perfect_totals
        
        records = parse_google_invoice_perfect(full_text, "5298528895.pdf")
        validation = validate_perfect_totals(records)
        
        print(f"   Records generated: {len(records)}")
        for i, record in enumerate(records, 1):
            print(f"     Record {i}: {record.get('item_type')} - {record.get('total')} - {record.get('description', '')[:50]}...")
        
        print(f"   Invoice total found: {validation.get('invoice_total')}")
        print(f"   Calculated total: {validation.get('calculated_total')}")
        print(f"   Validation: {validation.get('message')}")
        
    except Exception as e:
        print(f"   ERROR running parser: {e}")
        import traceback
        traceback.print_exc()

def debug_extract_invoice_total(text_content):
    """Debug the invoice total extraction process"""
    
    lines = text_content.split('\n')
    
    # Check if this is a credit note
    is_credit_note = False
    credit_keywords = ['credit note', 'credit memo', 'ใบลดหนี้', 'คืนเงิน']
    for line in lines[:50]:
        if any(keyword in line.lower() for keyword in credit_keywords):
            is_credit_note = True
            break
    
    print(f"   Is credit note: {is_credit_note}")
    
    # Extract all amounts
    all_amounts = []
    for line in lines:
        line_clean = line.strip()
        amounts_in_line = re.findall(r'฿?(-?[\d,]+\.\d{2})', line_clean)
        for amount_str in amounts_in_line:
            try:
                amount = float(amount_str.replace(',', ''))
                all_amounts.append(amount)
            except:
                continue
    
    print(f"   All amounts found: {all_amounts}")
    
    # Show frequency analysis
    amount_counter = Counter(all_amounts)
    most_common = amount_counter.most_common(10)
    print(f"   Amount frequencies: {most_common}")
    
    # Apply the logic from extract_invoice_total_perfect
    positive_amounts = [a for a in all_amounts if a > 0]
    
    if positive_amounts:
        amount_counter = Counter(positive_amounts)
        most_common_amounts = amount_counter.most_common(10)
        
        print(f"   Most frequent positive amounts: {most_common_amounts}")
        
        # Strategy 1: Most frequent amount that appears multiple times
        for amount, count in most_common_amounts:
            if count >= 2 and 100 < amount < 2000000:
                print(f"   Strategy 1 result: {amount} (appears {count} times)")
                return amount
        
        # Strategy 2: Largest reasonable amount
        reasonable_amounts = [a for a in positive_amounts if 100 < a < 2000000]
        if reasonable_amounts:
            max_amount = max(reasonable_amounts)
            print(f"   Strategy 2 result: {max_amount} (largest reasonable)")
            return max_amount
        
        print("   No suitable amount found using standard logic")
        return None
    else:
        print("   No positive amounts found")
        return None

def debug_ap_detection(text_content):
    """Debug AP detection logic"""
    
    # Strategy 1: Look for direct pk| patterns
    pk_direct = 'pk|' in text_content
    print(f"   Contains 'pk|': {pk_direct}")
    
    # Strategy 2: Look for p-k-| sequences
    lines = text_content.split('\n')
    pk_sequence_found = False
    
    for i in range(len(lines) - 2):
        if (lines[i].strip() == 'p' and 
            lines[i+1].strip() == 'k' and 
            lines[i+2].strip() == '|'):
            pk_sequence_found = True
            print(f"   Found p-k-| sequence at lines {i}-{i+2}")
            # Show context
            for j in range(max(0, i-2), min(len(lines), i+8)):
                marker = ">>> " if i <= j <= i+2 else "    "
                print(f"   {marker}{j:3d}: '{lines[j].strip()}'")
            break
    
    if not pk_sequence_found:
        print("   No p-k-| sequence found")
    
    is_ap = pk_direct or pk_sequence_found
    print(f"   Final AP detection: {'AP' if is_ap else 'Non-AP'}")

if __name__ == "__main__":
    debug_google_parser()