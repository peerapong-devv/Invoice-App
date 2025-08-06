#!/usr/bin/env python3
"""
Analyze the 5298528895.pdf file to understand why total extraction is failing
Expected total: 35,397.74 THB
"""

import fitz  # PyMuPDF
import re
import os

def analyze_pdf_structure(pdf_path):
    """Extract and analyze all text from the PDF"""
    print(f"Analyzing PDF: {pdf_path}")
    print("="*80)
    
    with fitz.open(pdf_path) as doc:
        print(f"Document has {len(doc)} pages")
        
        all_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            all_text += page_text
            
            print(f"\n--- PAGE {page_num + 1} ---")
            try:
                print(page_text)
            except UnicodeEncodeError:
                print(f"[Unicode content - {len(page_text)} characters]")
                # Print first 500 chars that can be encoded
                safe_text = page_text.encode('ascii', 'ignore').decode('ascii')
                print(safe_text[:500] + "..." if len(safe_text) > 500 else safe_text)
            print(f"--- END PAGE {page_num + 1} ---")
    
    return all_text

def search_for_total_patterns(text):
    """Search for various patterns that might contain the total amount"""
    print("\n" + "="*80)
    print("SEARCHING FOR TOTAL PATTERNS")
    print("="*80)
    
    # Look for the expected amount in various formats
    target_amount = "35,397.74"
    target_patterns = [
        r"35,397\.74",
        r"35397\.74", 
        r"35 397\.74",
        r"35\.397\.74",
        r"35,397 74",
        r"35397 74",
        r"35 397 74"
    ]
    
    print(f"\nSearching for target amount: {target_amount}")
    for pattern in target_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"  ✓ Found pattern '{pattern}': {matches}")
        else:
            print(f"  ✗ Pattern '{pattern}': No matches")
    
    # Look for general amount patterns
    print("\nSearching for all amount patterns:")
    amount_patterns = [
        r"\d{1,3}(?:,\d{3})*\.\d{2}",  # Standard format: 1,234.56
        r"\d+\.\d{2}",                 # Simple format: 1234.56
        r"\d{1,3}(?:\s\d{3})*\.\d{2}", # Space separated: 1 234.56
    ]
    
    all_amounts = set()
    for pattern in amount_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            all_amounts.add(match)
    
    print("All detected amounts:")
    for amount in sorted(all_amounts, key=lambda x: float(x.replace(',', '').replace(' ', ''))):
        print(f"  - {amount}")

def check_platform_detection(text):
    """Check if the platform is being detected correctly"""
    print("\n" + "="*80)
    print("PLATFORM DETECTION ANALYSIS") 
    print("="*80)
    
    keywords = {
        'Google': ['google', 'ads'],
        'Facebook': ['facebook', 'meta'],
        'TikTok': ['tiktok', 'bytedance']
    }
    
    text_lower = text.lower()
    for platform, words in keywords.items():
        found_words = [word for word in words if word in text_lower]
        if found_words:
            print(f"✓ {platform} detected (found: {found_words})")
        else:
            print(f"✗ {platform} not detected")

def check_ap_vs_nonap(text):
    """Check if it's being detected as AP vs Non-AP correctly"""
    print("\n" + "="*80)
    print("AP vs NON-AP DETECTION")
    print("="*80)
    
    is_ap = "[ST]" in text
    print(f"Contains '[ST]' marker: {'Yes' if is_ap else 'No'}")
    print(f"Invoice type should be: {'AP' if is_ap else 'Non-AP'}")
    
    if is_ap:
        # Count ST markers
        st_count = text.count('[ST]')
        print(f"Number of [ST] markers found: {st_count}")
        
        # Show lines with ST markers
        lines_with_st = [line.strip() for line in text.split('\n') if '[ST]' in line]
        print("\nLines containing [ST] markers:")
        for i, line in enumerate(lines_with_st, 1):
            print(f"  {i}: {line}")

def analyze_line_structure(text):
    """Analyze the line structure to understand parsing issues"""
    print("\n" + "="*80)
    print("LINE STRUCTURE ANALYSIS")
    print("="*80)
    
    lines = text.split('\n')
    print(f"Total lines in document: {len(lines)}")
    
    # Look for line numbers
    line_numbers = []
    for i, line in enumerate(lines):
        line = line.strip()
        if line.isdigit() and len(line) <= 3:
            line_numbers.append((i, int(line)))
    
    print(f"\nFound potential line numbers: {[num for _, num in line_numbers]}")
    
    # Show context around line numbers
    for line_idx, line_num in line_numbers:
        print(f"\nContext around line number {line_num} (line {line_idx}):")
        start = max(0, line_idx - 2)
        end = min(len(lines), line_idx + 5)
        for j in range(start, end):
            marker = ">>> " if j == line_idx else "    "
            print(f"{marker}{j:3d}: {lines[j].strip()}")

def look_for_totals_section(text):
    """Look for totals, subtotals, and invoice total sections"""
    print("\n" + "="*80)
    print("TOTALS SECTION ANALYSIS")
    print("="*80)
    
    total_keywords = [
        'total', 'subtotal', 'invoice total', 'grand total',
        'amount due', 'balance', 'sum', 'รวม'
    ]
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line_lower = line.strip().lower()
        for keyword in total_keywords:
            if keyword in line_lower:
                print(f"\nFound '{keyword}' at line {i}: {line.strip()}")
                # Show context
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                for j in range(start, end):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{j:3d}: {lines[j].strip()}")

def main():
    pdf_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\5298528895.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at {pdf_path}")
        return
    
    # Extract all text
    full_text = analyze_pdf_structure(pdf_path)
    
    # Run various analyses
    search_for_total_patterns(full_text)
    check_platform_detection(full_text)
    check_ap_vs_nonap(full_text)
    analyze_line_structure(full_text)
    look_for_totals_section(full_text)
    
    # Save the extracted text for further analysis
    output_file = "5298528895_extracted_text.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"\n\nFull extracted text saved to: {output_file}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()