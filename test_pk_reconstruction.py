#!/usr/bin/env python3
"""
Test if the pk reconstruction logic can handle this fragmented text
"""

import fitz
import re
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_reconstruction():
    pdf_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\5298528895.pdf"
    
    with fitz.open(pdf_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text()
    
    print("TESTING PK RECONSTRUCTION")
    print("=" * 60)
    
    # Import the reconstruction function
    try:
        from perfect_google_parser import reconstruct_pk_patterns_perfect, detect_ap_perfect
        
        print("Original text has pk|:", 'pk|' in full_text)
        
        # Test the reconstruction
        reconstructed_text = reconstruct_pk_patterns_perfect(full_text)
        
        print("After reconstruction has pk|:", 'pk|' in reconstructed_text)
        
        # Test AP detection on reconstructed text
        is_ap_original = detect_ap_perfect(full_text)
        is_ap_reconstructed = detect_ap_perfect(reconstructed_text)
        
        print(f"AP detection on original: {is_ap_original}")
        print(f"AP detection on reconstructed: {is_ap_reconstructed}")
        
        # Find pk| patterns in reconstructed text
        pk_patterns = re.findall(r'pk\|[^|]*\|[^|]*\|[^|]*', reconstructed_text)
        print(f"PK patterns found: {len(pk_patterns)}")
        
        for i, pattern in enumerate(pk_patterns, 1):
            try:
                print(f"  {i}: {pattern[:100]}...")
            except UnicodeEncodeError:
                safe_pattern = pattern.encode('ascii', 'ignore').decode('ascii')
                print(f"  {i}: {safe_pattern[:100]}...")
                
        # Save reconstructed text for inspection
        with open("5298528895_reconstructed.txt", 'w', encoding='utf-8') as f:
            f.write(reconstructed_text)
        print("\nReconstructed text saved to: 5298528895_reconstructed.txt")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reconstruction()