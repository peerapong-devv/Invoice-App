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

for indicator in strong_indicators:
    if indicator.lower() in text_lower:
        print(f"FOUND: '{indicator}' in text")
        # Find where it appears
        start = text_lower.find(indicator.lower())
        if start >= 0:
            context = text[max(0, start-50):start+len(indicator)+50]
            print(f"  Context: ...{context}...")
    else:
        print(f"NOT FOUND: '{indicator}'")

print("\n=== Sample text (first 1000 chars) ===")
print(text[:1000].encode('ascii', 'ignore').decode('ascii'))