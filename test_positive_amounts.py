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
    
    all_amounts = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        print(f"\n--- PAGE {page_num + 1} ---")
        
        # Look for ALL amounts (positive and negative)
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_clean = line.strip()
            line_ascii = line_clean.encode('ascii', 'ignore').decode('ascii')
            
            # Find all amounts (positive)
            positive_amounts = re.findall(r'(?<!\-)\b([\d,]+\.\d{2})\b', line_ascii)
            for amt in positive_amounts:
                try:
                    amount_value = float(amt.replace(',', ''))
                    if amount_value > 100:  # Reasonable invoice minimum
                        all_amounts.append(amount_value)
                        print(f"Positive amount at line {i}: {amt} ({amount_value}) -> '{line_ascii[:50]}...'")
                except:
                    continue
            
            # Find negative amounts
            negative_amounts = re.findall(r'-\s*([\d,]+\.\d{2})', line_ascii)
            for amt in negative_amounts:
                try:
                    amount_value = -float(amt.replace(',', ''))
                    all_amounts.append(amount_value)
                    print(f"Negative amount at line {i}: -{amt} ({amount_value}) -> '{line_ascii[:50]}...'")
                except:
                    continue
    
    print(f"\n=== All amounts found: ===")
    sorted_amounts = sorted(all_amounts, key=abs, reverse=True)
    for amt in sorted_amounts:
        print(f"  {amt:,.2f}")
    
    print(f"\nLargest positive amount: {max([a for a in all_amounts if a > 0], default=0):,.2f}")
    print(f"Most negative amount: {min([a for a in all_amounts if a < 0], default=0):,.2f}")
    print(f"Target: 18,550.72")