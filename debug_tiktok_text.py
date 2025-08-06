import fitz

# Read and print the actual text from TikTok invoice
pdf_path = "THTT202502215554-Prakit Holdings Public Company Limited-Invoice.pdf"

with fitz.open(pdf_path) as doc:
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"

# Check for AP markers
print("Checking for AP markers...")
print(f"Contains 'ST1150': {'ST1150' in full_text}")
print(f"Contains 'pk|': {'pk|' in full_text}")
print(f"Contains '[ST]': {'[ST]' in full_text}")

# Find the section with campaign details
start = full_text.find('Consumption Details:')
if start != -1:
    section = full_text[start:start+1000]
    print("\n=== First 1000 chars after 'Consumption Details:' ===")
    print(section)
    
# Look for ST pattern
import re
st_matches = re.findall(r'ST\d{10,}', full_text)
print(f"\nFound {len(st_matches)} ST patterns: {st_matches[:3]}")

# Look for pk| patterns
pk_matches = re.findall(r'pk\|[^\n]+', full_text)
print(f"\nFound {len(pk_matches)} pk| patterns:")
for i, match in enumerate(pk_matches[:3], 1):
    print(f"{i}. {match}")

# Save full text for analysis
with open('tiktok_debug.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)