import fitz
import sys
import os
sys.path.append('backend')
from app import parse_tiktok_text

# Quick test on 3 AP files to make sure no regression
ap_files = [
    'THTT202502215554-Prakit Holdings Public Company Limited-Invoice.pdf',
    'THTT202502215575-Prakit Holdings Public Company Limited-Invoice.pdf',
    'THTT202502216411-Prakit Holdings Public Company Limited-Invoice.pdf'
]

invoice_dir = r'C:\Users\peerapong\invoice-reader-app\Invoice for testing'
total_amount = 0
total_records = 0

for filename in ap_files:
    filepath = os.path.join(invoice_dir, filename)
    try:
        with fitz.open(filepath) as doc:
            text_content = '\n'.join([page.get_text() for page in doc])
        
        records = parse_tiktok_text(text_content, filename, 'TikTok')
        file_total = sum(record.get('total', 0) or 0 for record in records)
        total_amount += file_total
        total_records += len(records)
        
        # Count how many have project_id and campaign_id
        with_project_id = sum(1 for r in records if r.get('project_id'))
        with_campaign_id = sum(1 for r in records if r.get('campaign_id'))
        
        print(f'{filename[:12]}...: {len(records)} records, Total: {file_total:,.2f}')
        print(f'  Project IDs: {with_project_id}/{len(records)}, Campaign IDs: {with_campaign_id}/{len(records)}')
        
    except Exception as e:
        print(f'{filename}: ERROR - {e}')

print(f'\nOverall: {total_records} records, Total: {total_amount:,.2f} THB')
print('Expected AP total: 482,759.13 THB')
print(f'Match: {"YES" if abs(total_amount - 482759.13) < 1 else "NO"}')