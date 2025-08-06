import fitz
import re

# Check a few Google invoices to see if they have pk| pattern
test_files = [
    "Invoice for testing/5298248238.pdf",  # This one we know is AP
    "Invoice for testing/5297692778.pdf",
    "Invoice for testing/5298120337.pdf",
    "Invoice for testing/5300092128.pdf",
]

for pdf_file in test_files:
    print(f"\n=== Checking: {pdf_file} ===")
    
    try:
        with fitz.open(pdf_file) as doc:
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"
        
        # Check for Google markers
        has_google = "google" in full_text.lower() or "Google" in full_text
        has_ads = "ads" in full_text.lower() or "Ads" in full_text
        
        print(f"Has 'Google': {has_google}")
        print(f"Has 'Ads': {has_ads}")
        
        # Check for pk| patterns
        pk_direct = "pk|" in full_text
        pk_spaced = "pk |" in full_text or "p k|" in full_text
        pk_newline = bool(re.search(r'p\s*\n\s*k\s*\n?\s*\|', full_text))
        
        print(f"Has direct 'pk|': {pk_direct}")
        print(f"Has spaced 'pk |': {pk_spaced}")
        print(f"Has newline pk pattern: {pk_newline}")
        
        # Look for any pk patterns
        pk_patterns = re.findall(r'p\s*k\s*\|[^\n]{0,50}', full_text[:2000])
        if pk_patterns:
            print(f"Found pk patterns: {len(pk_patterns)}")
            print(f"First pattern: {pk_patterns[0][:50]}")
        
        # Check the specific area where pk| usually appears
        if "คำอธิบาย" in full_text or "Description" in full_text:
            desc_pos = full_text.find("คำอธิบาย")
            if desc_pos == -1:
                desc_pos = full_text.find("Description")
            
            if desc_pos > 0:
                section = full_text[desc_pos:desc_pos+500]
                print(f"\nSection after 'Description':")
                print(section[:200])
                
    except Exception as e:
        print(f"Error: {e}")