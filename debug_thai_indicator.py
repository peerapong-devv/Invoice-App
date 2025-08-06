import fitz

filename = '5297692778.pdf'
with fitz.open(f'Invoice for testing/{filename}') as doc:
    text = ''.join([page.get_text() for page in doc])

# Check Thai indicators by converting to bytes and searching
text_bytes = text.encode('utf-8', 'ignore')

thai_indicators = [
    'กิจกรรมที่ไม่ถูกต้อง'.encode('utf-8'),
    'ใบลดหนี้'.encode('utf-8'),
    'หมายเลขใบแจ้งหนี้เดิม'.encode('utf-8')
]

print("Checking Thai indicators...")
for indicator in thai_indicators:
    if indicator in text_bytes:
        print(f"FOUND Thai indicator: {len(indicator)} bytes")
        # Find position
        pos = text_bytes.find(indicator)
        context_bytes = text_bytes[max(0, pos-50):pos+len(indicator)+50]
        try:
            context = context_bytes.decode('utf-8', 'ignore')
            print(f"Context: {context}")
        except:
            print("Could not decode context")
    else:
        print(f"NOT FOUND: Thai indicator")

# Also check English
english_indicators = ['original invoice', 'credit note', 'invalid activity']
text_lower = text.lower()
for indicator in english_indicators:
    if indicator in text_lower:
        print(f"FOUND English: {indicator}")
    else:
        print(f"NOT FOUND English: {indicator}")