import fitz
import sys
import re
sys.path.append('backend')

filename = '5297692778.pdf'
with fitz.open(f'Invoice for testing/{filename}') as doc:
    text = '\n'.join([page.get_text() for page in doc])

# Strong credit indicators (must have these to be considered credit note)
strong_indicators = [
    'กิจกรรมที่ไม่ถูกต้อง',
    'ใบลดหนี้',
    'หมายเลขใบแจ้งหนี้เดิม',
    'credit note',
    'credit memo',
    'invalid activity',
    'original invoice'
]

text_lower = text.lower()

# Check for strong credit indicators first
has_strong_indicator = any(indicator.lower() in text_lower for indicator in strong_indicators)
print(f"has_strong_indicator: {has_strong_indicator}")

if has_strong_indicator:
    print("Would return True (has strong indicator)")
else:
    print("No strong indicator, checking amounts...")
    
    lines = text.split('\n')
    positive_amounts = []
    negative_amounts = []
    
    for line in lines:
        line_ascii = line.strip().encode('ascii', 'ignore').decode('ascii')
        
        # Find positive amounts
        pos_amounts = re.findall(r'([0-9,]+\.[0-9]{2})', line_ascii)
        for amt_str in pos_amounts:
            if '-' not in line_ascii or line_ascii.find(amt_str) < line_ascii.find('-'):
                try:
                    amount = float(amt_str.replace(',', ''))
                    if amount > 100:  # Significant amounts
                        positive_amounts.append(amount)
                except:
                    continue
        
        # Find negative amounts
        if '-' in line_ascii:
            neg_amounts = re.findall(r'-\s*([0-9,]+\.[0-9]{2})', line_ascii)
            for amt_str in neg_amounts:
                try:
                    amount = float(amt_str.replace(',', ''))
                    if amount > 1:  # Any negative amount
                        negative_amounts.append(amount)
                except:
                    continue
    
    print(f"positive_amounts: {len(positive_amounts)} items, max: {max(positive_amounts) if positive_amounts else 0}")
    print(f"negative_amounts: {len(negative_amounts)} items")
    
    # Check conditions
    condition1 = positive_amounts and max(positive_amounts) > 1000
    print(f"condition1 (pos > 1000): {condition1}")
    
    if condition1:
        print("Would return False (regular invoice)")
    else:
        condition2 = negative_amounts and (not positive_amounts or max(positive_amounts) <= 1000)
        print(f"condition2 (credit note): {condition2}")
        if condition2:
            print("Would return True (credit note)")
        else:
            print("Would return False (default)")