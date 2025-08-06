import fitz
import sys
import re
sys.path.append('backend')

# Test specific file that should be positive but showing negative
filename = '5297692778.pdf'
filepath = f'Invoice for testing/{filename}'

print(f"=== Testing {filename} - should be 18,550.72 THB ===")

with fitz.open(filepath) as doc:
    print(f"Total pages: {len(doc)}")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        print(f"\n--- PAGE {page_num + 1} ---")
        
        # Look for total amount patterns - encode as ASCII to avoid Thai issues
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_ascii = line_clean.encode('ascii', 'ignore').decode('ascii')
            
            # Look for amounts with THB
            thb_amounts = re.findall(r'([\d,]+\.?\d*)\s*THB', line_ascii)
            if thb_amounts:
                print(f"THB amount at line {i}: {thb_amounts} -> '{line_ascii}'")
            
            # Look for amounts with baht symbol
            baht_amounts = re.findall(r'([\d,]+\.?\d*)', line_ascii)
            if baht_amounts and 'THB' in line_ascii:
                print(f"Amount with THB at line {i}: {baht_amounts} -> '{line_ascii}'")
            
            # Look for specific total patterns
            if any(keyword in line_ascii for keyword in ['Total', 'amount', 'due']):
                print(f"Total keyword at line {i}: '{line_ascii}'")
            
            # Look for negative amounts
            if '-' in line_ascii and any(c.isdigit() for c in line_ascii):
                amounts = re.findall(r'-\s*([\d,]+\.?\d*)', line_ascii)
                if amounts:
                    print(f"Negative amount at line {i}: {amounts} -> '{line_ascii}'")
            
            # Look for pk patterns
            if 'pk' in line_ascii.lower():
                print(f"PK pattern at line {i}: '{line_ascii}'")