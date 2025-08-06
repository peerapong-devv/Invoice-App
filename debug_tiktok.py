import fitz
import sys
import re
sys.path.append('backend')

# Extract raw text from the problematic file
filepath = r'C:\Users\peerapong\invoice-reader-app\Invoice for testing\THTT202502215554-Prakit Holdings Public Company Limited-Invoice.pdf'
with fitz.open(filepath) as doc:
    text_content = '\n'.join([page.get_text() for page in doc])

# Find consumption details section
consumption_start = text_content.find('Consumption Details:')
if consumption_start != -1:
    consumption_text = text_content[consumption_start:]
    
    # Find all ST patterns
    st_pattern = re.compile(r'(ST\d{10,})')
    st_matches = list(st_pattern.finditer(consumption_text))
    
    print(f'Found {len(st_matches)} ST patterns')
    
    # Show all ST sections
    for i, st_match in enumerate(st_matches, 1):
        start_pos = st_match.start()
        
        # Find end position
        if i < len(st_matches):
            end_pos = st_matches[i].start()
        else:
            subtotal_match = re.search(r'Subtotal', consumption_text[start_pos:])
            if subtotal_match:
                end_pos = start_pos + subtotal_match.start()
            else:
                end_pos = len(consumption_text)
        
        section = consumption_text[start_pos:end_pos]
        print(f'\n=== ST Section {i} ===')
        print(f'ST ID: {st_match.group(1)}')
        print(f'Raw section (first 200 chars):')
        print(repr(section[:200]))
        print()