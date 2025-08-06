#!/usr/bin/env python3

import os
import sys
import PyPDF2
import re
from collections import Counter

# Add backend to path
sys.path.append('./backend')

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyPDF2"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        return f"Error: {str(e)}"

def accurate_platform_detection(text_content, filename):
    """Accurate platform detection"""
    
    # First check for TikTok (must be more specific - filename or company name)
    if (filename.startswith('THTT') or 
        'TIKTOK PTE. LTD' in text_content):
        return "TikTok"
    
    # Then check for Google (including filename patterns)
    if (('google' in text_content.lower() and 'ads' in text_content.lower()) or
        filename.startswith('529') or filename.startswith('530')):
        return "Google"
    
    # Then check for Facebook
    if ('facebook' in text_content.lower() or 'meta' in text_content.lower() or 
        'Meta Platforms' in text_content or
        (filename.startswith('246') and not filename.startswith('THTT'))):
        return "Facebook"
    
    return "Unknown"

def parse_google_amount(text_content, filename):
    """Parse Google invoice amount - try multiple approaches"""
    
    amounts = []
    lines = text_content.split('\n')
    
    # Look for various patterns
    for line in lines:
        # Find all amounts
        matches = re.findall(r'[\d,]+\.\d{2}', line)
        for match in matches:
            try:
                amount = float(match.replace(',', ''))
                if amount > 0:
                    amounts.append(amount)
            except:
                continue
    
    if amounts:
        # Use the most frequent amount as invoice total
        amount_freq = Counter(amounts)
        most_frequent = amount_freq.most_common(1)[0]
        return most_frequent[0]
    
    return 0

def check_google_total():
    """Check Google invoice total"""
    
    invoice_dir = "./Invoice for testing"
    
    if not os.path.exists(invoice_dir):
        print(f"Error: Directory not found: {invoice_dir}")
        return
    
    # Get ALL PDF files
    all_files = [f for f in os.listdir(invoice_dir) if f.endswith('.pdf')]
    
    # Find Google files
    google_files = []
    for filename in sorted(all_files):
        pdf_path = os.path.join(invoice_dir, filename)
        text_content = extract_text_from_pdf(pdf_path)
        
        if text_content.startswith("Error"):
            continue
        
        platform = accurate_platform_detection(text_content, filename)
        
        if platform == "Google":
            google_files.append((filename, text_content))
    
    print(f"Found {len(google_files)} Google files")
    print("="*60)
    
    total_amount = 0
    for filename, text_content in google_files:
        amount = parse_google_amount(text_content, filename)
        total_amount += amount
        print(f"{filename}: {amount:,.2f} THB")
    
    print("="*60)
    print(f"Total Google amount: {total_amount:,.2f} THB")
    print(f"Expected amount: 2,362,684.79 THB")
    print(f"Difference: {2362684.79 - total_amount:,.2f} THB")

if __name__ == "__main__":
    check_google_total()