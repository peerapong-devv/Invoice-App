#!/usr/bin/env python3

import os
from PyPDF2 import PdfReader

def analyze_ap_files():
    """Analyze what makes an AP vs Non-AP file"""
    
    # From the test results, we know these are AP files
    known_ap_files = [
        "5298248238.pdf",
        "5297692787.pdf", 
        "5297692799.pdf",
        "5298130144.pdf",
        "5298240989.pdf"
    ]
    
    # Known Non-AP files
    known_non_ap_files = [
        "5297735036.pdf",
        "5298156820.pdf", 
        "5300646032.pdf"
    ]
    
    def analyze_file(filename, expected_type):
        filepath = os.path.join("Invoice for testing", filename)
        
        if not os.path.exists(filepath):
            print(f"  File not found: {filename}")
            return
            
        try:
            with open(filepath, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                text_content = ''.join([page.extract_text() for page in reader.pages])
            
            print(f"\n{filename} ({expected_type}):")
            print(f"  Length: {len(text_content)} chars")
            
            # Check for various AP indicators
            has_pk_pipe = 'pk|' in text_content
            has_pk_space = 'pk ' in text_content.lower()
            has_p_k_pattern = '\np\nk\n|' in text_content or 'p\nk\n|' in text_content
            has_agency_pattern = text_content.count('pk') > 5
            has_campaign_id = any(word in text_content.lower() for word in ['campaign', 'แคมเปญ', 'project'])
            
            print(f"  Has 'pk|': {has_pk_pipe}")
            print(f"  Has 'pk ': {has_pk_space}")
            print(f"  Has p\\nk\\n| pattern: {has_p_k_pattern}")
            print(f"  Multiple 'pk' mentions: {has_agency_pattern} (count: {text_content.count('pk')})")
            print(f"  Has campaign/project words: {has_campaign_id}")
            
            # Look for line-by-line patterns
            lines = text_content.split('\n')
            pk_lines = [line for line in lines if 'pk' in line.lower()]
            if pk_lines:
                print(f"  Lines with 'pk': {len(pk_lines)}")
                for i, line in enumerate(pk_lines[:3]):
                    print(f"    {i+1}: {line.strip()}")
            
            # Look for fragmented pk patterns
            if not has_pk_pipe and expected_type == "AP":
                print("  Looking for fragmented patterns:")
                for i, line in enumerate(lines):
                    if line.strip() == 'p' and i+2 < len(lines):
                        if lines[i+1].strip() == 'k' and lines[i+2].strip() == '|':
                            print(f"    Found p-k-| sequence at lines {i}-{i+2}")
                            # Show next few lines
                            for j in range(i+3, min(len(lines), i+8)):
                                if lines[j].strip():
                                    print(f"      {j}: {lines[j].strip()}")
                            break
                            
        except Exception as e:
            print(f"  Error: {e}")
    
    print("ANALYZING KNOWN AP FILES:")
    print("="*50)
    
    for filename in known_ap_files:
        analyze_file(filename, "AP")
    
    print("\n\nANALYZING KNOWN NON-AP FILES:")
    print("="*50)
    
    for filename in known_non_ap_files:
        analyze_file(filename, "Non-AP")

if __name__ == "__main__":
    analyze_ap_files()