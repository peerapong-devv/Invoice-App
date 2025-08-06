import fitz
import sys
import os
sys.path.append('backend')
from app import parse_google_text

# Test files with known issues
test_files = [
    '5297692778.pdf',  # Spacing issues: pk|4 0 1 0 9 | S D H
    '5298528895.pdf',   # Zero amounts problem
    '5297692787.pdf'    # Should work fine (baseline)
]

invoice_dir = r'C:\Users\peerapong\invoice-reader-app\Invoice for testing'

for filename in test_files:
    print(f'\n=== Testing {filename} ===')
    try:
        filepath = os.path.join(invoice_dir, filename)
        with fitz.open(filepath) as doc:
            text_content = '\n'.join([page.get_text() for page in doc])

        records = parse_google_text(text_content, filename, 'Google')
        
        print(f'Found {len(records)} records')
        if records:
            total_amount = sum(record.get('total', 0) or 0 for record in records)
            print(f'Total amount: {total_amount:,.2f} THB')
            
            # Check for spacing issues
            for i, record in enumerate(records[:2]):  # Show first 2 records
                project_id = record.get('project_id', '')
                campaign_id = record.get('campaign_id', '')
                has_spaces = ' ' in str(project_id) or ' ' in str(campaign_id)
                print(f'Record {i+1}: Project ID: "{project_id}", Campaign ID: "{campaign_id}"')
                if has_spaces:
                    print(f'  ⚠️  Contains spacing issues')
                else:
                    print(f'  ✅ Clean IDs')
        else:
            print('No records found')
                
    except Exception as e:
        print(f'ERROR: {e}')