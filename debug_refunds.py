import fitz
import re

def debug_refund_detection(pdf_path):
    """Debug why refunds are not being detected"""
    
    print(f"=== DEBUG REFUNDS: {pdf_path} ===\n")
    
    with fitz.open(pdf_path) as doc:
        full_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            full_text += page_text + f"\n--- PAGE {page_num + 1} END ---\n"
    
    print(f"Total text length: {len(full_text)}")
    
    # Clean text
    clean_text = full_text.replace('\u200b', '')
    
    # Look specifically for negative amounts
    print("\n=== SEARCHING FOR NEGATIVE AMOUNTS ===")
    
    # Pattern 1: Lines ending with negative amounts
    negative_pattern1 = r'^(.+?)\s+([-]\d+\.\d{2})$'
    neg_matches1 = re.findall(negative_pattern1, clean_text, re.MULTILINE)
    
    print(f"Pattern 1 (ends with -amount): Found {len(neg_matches1)} matches")
    for i, (desc, amount) in enumerate(neg_matches1, 1):
        print(f"  {i}. '{desc}' -> {amount}")
    
    # Pattern 2: Look for minus signs anywhere
    minus_pattern = r'.*[-]\d+\.\d{2}.*'
    minus_matches = re.findall(minus_pattern, clean_text, re.MULTILINE)
    
    print(f"\nPattern 2 (contains -amount): Found {len(minus_matches)} matches")
    for i, match in enumerate(minus_matches[:5], 1):
        print(f"  {i}. {match[:80]}...")
    
    # Pattern 3: Look for amounts in parentheses (sometimes used for negatives)
    paren_pattern = r'^(.+?)\s+\(([\d,]+\.\d{2})\)$'
    paren_matches = re.findall(paren_pattern, clean_text, re.MULTILINE)
    
    print(f"\nPattern 3 ((amount) format): Found {len(paren_matches)} matches")
    for i, (desc, amount) in enumerate(paren_matches, 1):
        print(f"  {i}. '{desc}' -> ({amount})")
    
    # Pattern 4: Look for any line with negative numbers
    any_negative = r'.*-[\d,]+\.?\d*.*'
    any_neg_matches = re.findall(any_negative, clean_text, re.MULTILINE)
    
    print(f"\nPattern 4 (any negative): Found {len(any_neg_matches)} matches")
    for i, match in enumerate(any_neg_matches[:10], 1):
        try:
            print(f"  {i}. {match[:60]}...")
        except UnicodeEncodeError:
            print(f"  {i}. [Unicode text with negative]")
    
    # Let's look at the raw lines around where we expect refunds
    print(f"\n=== RAW LINES ANALYSIS ===")
    lines = clean_text.split('\n')
    
    # Look for lines that contain negative numbers
    negative_lines = []
    for i, line in enumerate(lines):
        if '-' in line and re.search(r'-[\d,]*\.?\d+', line):
            negative_lines.append((i, line.strip()))
    
    print(f"Found {len(negative_lines)} lines with negative numbers:")
    for i, (line_num, line) in enumerate(negative_lines[:10], 1):
        try:
            print(f"  Line {line_num}: {line[:80]}...")
        except UnicodeEncodeError:
            print(f"  Line {line_num}: [Unicode text with negative]")
    
    # Try the exact pattern from the full analysis
    print(f"\n=== USING EXACT PATTERN FROM ANALYSIS ===")
    amount_pattern = r'^(.+?)\s+([-]?[\d,]+\.\d{2})$'
    all_matches = re.findall(amount_pattern, clean_text, re.MULTILINE)
    
    print(f"All financial matches: {len(all_matches)}")
    negatives_found = []
    for desc, amount_str in all_matches:
        amount = float(amount_str.replace(',', ''))
        if amount < 0:
            negatives_found.append((desc, amount))
    
    print(f"Negative amounts found: {len(negatives_found)}")
    for i, (desc, amount) in enumerate(negatives_found, 1):
        try:
            print(f"  {i}. '{desc[:50]}...' -> {amount}")
        except UnicodeEncodeError:
            print(f"  {i}. [Unicode] -> {amount}")

# Debug the specific file
debug_refund_detection("Invoice for testing/5297692787.pdf")