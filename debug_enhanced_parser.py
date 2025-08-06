import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import fitz
from enhanced_google_parser import parse_google_invoice_enhanced

def debug_parser(pdf_path):
    """Debug the enhanced parser step by step"""
    
    print(f"=== Debugging: {pdf_path} ===\n")
    
    # Extract text
    with fitz.open(pdf_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
    
    print(f"Original text length: {len(full_text)}")
    
    # Test the parser
    try:
        records = parse_google_invoice_enhanced(full_text, pdf_path)
        print(f"Parser returned {len(records)} records")
        
        for i, record in enumerate(records, 1):
            print(f"\nRecord {i}:")
            print(f"  Description: {record.get('description', 'N/A')[:50]}...")
            print(f"  Amount: {record.get('total', 'N/A')}")
            print(f"  Item Type: {record.get('item_type', 'N/A')}")
            print(f"  Invoice Total: {record.get('invoice_total', 'N/A')}")
        
    except Exception as e:
        print(f"Parser error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check text patterns manually
    print(f"\n=== Manual Pattern Check ===")
    
    # Clean text
    clean_text = full_text.replace('\u200b', '')
    
    # Look for amounts
    import re
    amount_pattern = r'^(.+?)\s+([-]?\d{1,3}(?:,\d{3})*\.\d{2})$'
    matches = re.findall(amount_pattern, clean_text, re.MULTILINE)
    
    print(f"Found {len(matches)} potential amount lines:")
    
    for i, (desc, amount) in enumerate(matches[:10], 1):
        print(f"  {i}. {desc[:40]}... -> {amount}")
    
    # Look for pk| patterns
    pk_matches = re.findall(r'pk\|[^\n]+', clean_text)
    print(f"\nFound {len(pk_matches)} pk| patterns:")
    for i, match in enumerate(pk_matches[:3], 1):
        print(f"  {i}. {match[:50]}...")

# Test on the problematic file
debug_parser("Invoice for testing/5298248238.pdf")