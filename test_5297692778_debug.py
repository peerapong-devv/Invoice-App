import fitz
import sys
import os
sys.path.append('backend')
from improved_google_parser import parse_google_invoice_improved, validate_improved_totals

# Test the specific problematic file
filename = '5297692778.pdf'
filepath = os.path.join('Invoice for testing', filename)

print(f'=== Debugging {filename} ===')
try:
    with fitz.open(filepath) as doc:
        text_content = '\n'.join([page.get_text() for page in doc])

    # Save all lines to see the structure and look for pk patterns
    lines = text_content.split('\n')
    print("Lines 80-150 to find pk patterns:")
    pk_found_lines = []
    
    for i, line in enumerate(lines[79:150]):  # Lines 80-150
        clean_line = line.strip().encode('ascii', 'ignore').decode('ascii')
        line_num = i + 80
        if clean_line:
            print(f"Line {line_num}: '{clean_line}'")
            # Look for pk patterns or single character lines
            if 'pk' in clean_line.lower() or 'p k' in clean_line.lower() or len(clean_line) == 1:
                pk_found_lines.append((line_num, clean_line))
    
    print(f"\n=== Lines containing 'pk' patterns: ===")
    for line_num, line_content in pk_found_lines:
        print(f"Line {line_num}: '{line_content}'")

    print("\n=== Running improved parser ===")
    records = parse_google_invoice_improved(text_content, filename)
    validation = validate_improved_totals(records)
    
    print(f'Found {len(records)} records')
    print(f'Validation: {validation["message"]}')
    
    for i, record in enumerate(records, 1):
        print(f'Record {i}:')
        print(f'  Project ID: "{record.get("project_id")}"')
        print(f'  Campaign ID: "{record.get("campaign_id")}"')
        print(f'  Project Name: "{record.get("project_name")}"')
        print(f'  Amount: {record.get("total")}')
        print(f'  Description: {record.get("description", "")[:100]}...')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()