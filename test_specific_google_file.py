import fitz
import sys
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
        
        # Look for total amount patterns
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Look for invoice total patterns
            if any(keyword in line_clean for keyword in ['รวม', 'THB', 'Total', 'amount', '฿']):
                print(f"Line {i}: {line_clean}")
                
                # Check next few lines too
                for j in range(i, min(i+3, len(lines))):
                    next_line = lines[j].strip()
                    if any(c.isdigit() for c in next_line):
                        print(f"  -> {next_line}")
            
            # Look for pk patterns
            if 'pk' in line_clean.lower() or line_clean == 'p':
                print(f"PK pattern at line {i}: {line_clean}")
                if i + 1 < len(lines):
                    print(f"  Next: {lines[i+1].strip()}")
            
            # Look for credit/refund indicators
            if any(word in line_clean.lower() for word in ['credit', 'refund', 'กิจกรรมที่ไม่ถูกต้อง', 'ใบลดหนี้']):
                print(f"Credit indicator at line {i}: {line_clean}")
            
            # Look for negative amounts
            if '-' in line_clean and any(c.isdigit() for c in line_clean):
                print(f"Negative amount at line {i}: {line_clean}")