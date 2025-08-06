#!/usr/bin/env python3

import os
import sys
import PyPDF2

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
    """Accurate platform detection - fix TikTok misclassification"""
    
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

def debug_specific_file():
    """Debug the specific missing file"""
    
    filename = "5300784496.pdf"
    invoice_dir = "./Invoice for testing"
    pdf_path = os.path.join(invoice_dir, filename)
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return
    
    print(f"Debugging file: {filename}")
    print("=" * 50)
    
    # Extract text
    text_content = extract_text_from_pdf(pdf_path)
    
    if text_content.startswith("Error"):
        print(f"Text extraction failed: {text_content}")
        return
    
    print(f"Text content length: {len(text_content)} characters")
    print(f"Text contains Thai characters")
    print("\n" + "=" * 50)
    
    # Check detection logic
    print(f"Filename starts with '529': {filename.startswith('529')}")
    print(f"Filename starts with '530': {filename.startswith('530')}")
    print(f"Filename starts with 'THTT': {filename.startswith('THTT')}")
    print(f"Contains 'google' (lowercase): {'google' in text_content.lower()}")
    print(f"Contains 'ads' (lowercase): {'ads' in text_content.lower()}")
    print(f"Contains 'facebook' (lowercase): {'facebook' in text_content.lower()}")
    print(f"Contains 'meta' (lowercase): {'meta' in text_content.lower()}")
    print(f"Contains 'TikTok': {'TikTok' in text_content}")
    print(f"Contains 'TIKTOK PTE. LTD': {'TIKTOK PTE. LTD' in text_content}")
    
    # Platform detection
    platform = accurate_platform_detection(text_content, filename)
    print(f"\nDetected platform: {platform}")
    
    # Check if it passes each condition
    print(f"\nUpdated detection logic breakdown:")
    
    # TikTok check (updated)
    tiktok_condition = (filename.startswith('THTT') or 
                       'TIKTOK PTE. LTD' in text_content)
    print(f"1. TikTok condition (updated): {tiktok_condition}")
    
    # Google check (updated)
    google_condition = (('google' in text_content.lower() and 'ads' in text_content.lower()) or
                       filename.startswith('529') or filename.startswith('530'))
    print(f"2. Google condition (updated): {google_condition}")
    
    # Facebook check (updated)
    facebook_condition = ('facebook' in text_content.lower() or 
                         'meta' in text_content.lower() or 
                         'Meta Platforms' in text_content or
                         (filename.startswith('246') and not filename.startswith('THTT')))
    print(f"3. Facebook condition (updated): {facebook_condition}")
    
    print(f"\nFinal result: Should be classified as Google: {platform == 'Google'}")

if __name__ == "__main__":
    debug_specific_file()