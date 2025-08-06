import fitz
import sys
sys.path.append('backend')

filename = '5297692778.pdf'
with fitz.open(f'Invoice for testing/{filename}') as doc:
    text = '\n'.join([page.get_text() for page in doc])

print("=== Checking for credit indicators ===")

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
found_any = False

for indicator in strong_indicators:
    if indicator.lower() in text_lower:
        print(f"FOUND: {indicator}")
        found_any = True
    else:
        print(f"NOT FOUND: {indicator}")

print(f"\nAny strong indicators found: {found_any}")

# Check amounts
import re
lines = text.split('\n')
positive_amounts = []
negative_amounts = []

for line in lines:
    line_ascii = line.strip().encode('ascii', 'ignore').decode('ascii')
    
    # Find positive amounts
    pos_amounts = re.findall(r'(?<!\-)\b([\d,]+\.\d{2})\b', line_ascii)
    for amt_str in pos_amounts:
        try:
            amount = float(amt_str.replace(',', ''))
            if amount > 100:
                positive_amounts.append(amount)
        except:
            continue
    
    # Find negative amounts
    neg_amounts = re.findall(r'-\s*([\d,]+\.\d{2})', line_ascii)
    for amt_str in neg_amounts:
        try:
            amount = float(amt_str.replace(',', ''))
            if amount > 1:
                negative_amounts.append(amount)
        except:
            continue

print(f"\nPositive amounts > 100: {sorted(set(positive_amounts), reverse=True)[:5]}")
print(f"Negative amounts: {sorted(set(negative_amounts), reverse=True)}")
print(f"Max positive: {max(positive_amounts) if positive_amounts else 0}")
print(f"Should be credit note: {not (positive_amounts and max(positive_amounts) > 1000)}")