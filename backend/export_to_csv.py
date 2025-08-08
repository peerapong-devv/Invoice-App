#!/usr/bin/env python3
"""Export invoice report to CSV format"""

import json
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load the report
with open('all_138_files_updated_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Create CSV file with all invoice details
csv_filename = 'invoice_report.csv'
with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
    fieldnames = [
        'filename',
        'platform',
        'invoice_type',
        'invoice_number',
        'line_number',
        'description',
        'amount',
        'agency',
        'project_id',
        'project_name',
        'campaign_id',
        'objective',
        'period'
    ]
    
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    # Write each invoice item
    for filename, file_data in report['files'].items():
        for item in file_data['items']:
            row = {
                'filename': filename,
                'platform': item.get('platform', ''),
                'invoice_type': item.get('invoice_type', ''),
                'invoice_number': item.get('invoice_number', ''),
                'line_number': item.get('line_number', ''),
                'description': item.get('description', ''),
                'amount': item.get('amount', 0),
                'agency': item.get('agency', ''),
                'project_id': item.get('project_id', ''),
                'project_name': item.get('project_name', ''),
                'campaign_id': item.get('campaign_id', ''),
                'objective': item.get('objective', ''),
                'period': item.get('period', '')
            }
            writer.writerow(row)

print(f"CSV file created: {csv_filename}")

# Create summary CSV
summary_csv = 'invoice_summary.csv'
with open(summary_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)
    
    # Write header
    writer.writerow(['Platform', 'Files', 'Items', 'Total Amount (THB)', 'Avg Items/File'])
    
    # Write platform summaries
    for platform, data in report['summary']['by_platform'].items():
        writer.writerow([
            platform,
            data['files'],
            data['total_items'],
            f"{data['total_amount']:,.2f}",
            data.get('average_items_per_file', 0)
        ])
    
    # Write total
    writer.writerow([])
    writer.writerow([
        'TOTAL',
        report['summary']['overall']['files_processed'],
        report['summary']['overall']['total_items'],
        f"{report['summary']['overall']['total_amount']:,.2f}",
        ''
    ])

print(f"Summary CSV created: {summary_csv}")

# Create file-level summary CSV
file_summary_csv = 'invoice_file_summary.csv'
with open(file_summary_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
    fieldnames = ['filename', 'platform', 'invoice_type', 'items_count', 'total_amount']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for filename, file_data in report['files'].items():
        writer.writerow({
            'filename': filename,
            'platform': file_data['platform'],
            'invoice_type': file_data['invoice_type'],
            'items_count': file_data['items_count'],
            'total_amount': f"{file_data['total_amount']:,.2f}"
        })

print(f"File summary CSV created: {file_summary_csv}")
print("\nAll CSV files created successfully!")