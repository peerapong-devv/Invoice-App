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
    
    # Show the problematic 5th ST section (Record 4)
    if len(st_matches) >= 5:
        st_match = st_matches[4]  # 5th item (index 4)
        start_pos = st_match.start()
        end_pos = len(consumption_text)  # Last section, go to end
        
        section = consumption_text[start_pos:end_pos]
        print('=== ST Section 5 (Record 4) Full Raw Data ===')
        print(repr(section))
        
        # Also show lines individually
        print('\n=== Lines breakdown ===')
        lines = section.split('\n')
        for i, line in enumerate(lines):
            print(f'Line {i}: {repr(line)}')