#!/usr/bin/env python3
"""Generate updated comprehensive report after all parser fixes"""

import os
import sys
import json
import fitz
from datetime import datetime

# Import the fixed parsers
from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed
from google_parser_professional import parse_google_invoice
from facebook_parser_complete import parse_facebook_invoice

sys.stdout.reconfigure(encoding='utf-8')

def process_all_invoices():
    """Process all invoice files with updated parsers"""
    
    invoice_dir = os.path.join('..', 'Invoice for testing')
    all_files = sorted([f for f in os.listdir(invoice_dir) if f.endswith('.pdf')])
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_files': len(all_files),
        'summary': {
            'by_platform': {},
            'overall': {
                'total_amount': 0,
                'total_items': 0,
                'files_processed': 0
            }
        },
        'files': {}
    }
    
    print(f"Processing {len(all_files)} invoice files...")
    print("="*80)
    
    for idx, filename in enumerate(all_files):
        filepath = os.path.join(invoice_dir, filename)
        
        # Read text content
        try:
            with fitz.open(filepath) as doc:
                text_content = ""
                for page in doc:
                    text_content += page.get_text()
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue
        
        # Determine platform and parse
        # Google files start with 5
        if filename.startswith('5'):
            platform = 'Google'
            records = parse_google_invoice(text_content, filepath)
        # TikTok files start with THTT
        elif filename.startswith('THTT') or "tiktok" in text_content.lower():
            platform = 'TikTok'
            records = parse_tiktok_invoice_detailed(text_content, filename)
        # Facebook files start with 24
        elif filename.startswith('24') or "facebook" in text_content.lower() or "meta" in text_content.lower():
            platform = 'Facebook'
            records = parse_facebook_invoice(text_content, filename)
        else:
            platform = 'Unknown'
            records = []
        
        # Calculate totals
        file_total = sum(record.get('amount', 0) for record in records)
        
        # Store file data
        report['files'][filename] = {
            'platform': platform,
            'invoice_type': records[0].get('invoice_type', 'Unknown') if records else 'Unknown',
            'invoice_number': records[0].get('invoice_number', 'Unknown') if records else 'Unknown',
            'total_items': len(records),
            'total_amount': file_total,
            'items': records
        }
        
        # Update platform summary
        if platform not in report['summary']['by_platform']:
            report['summary']['by_platform'][platform] = {
                'files': 0,
                'total_items': 0,
                'total_amount': 0,
                'average_items_per_file': 0
            }
        
        report['summary']['by_platform'][platform]['files'] += 1
        report['summary']['by_platform'][platform]['total_items'] += len(records)
        report['summary']['by_platform'][platform]['total_amount'] += file_total
        
        # Update overall summary
        report['summary']['overall']['total_amount'] += file_total
        report['summary']['overall']['total_items'] += len(records)
        report['summary']['overall']['files_processed'] += 1
        
        # Progress indicator
        print(f"[{idx+1:3d}/{len(all_files)}] {filename} - {platform}: {len(records)} items, {file_total:,.2f} THB")
    
    # Calculate averages
    for platform, data in report['summary']['by_platform'].items():
        if data['files'] > 0:
            data['average_items_per_file'] = round(data['total_items'] / data['files'], 2)
    
    return report

# Generate the report
print("GENERATING UPDATED COMPREHENSIVE REPORT")
print("="*80)

report = process_all_invoices()

# Save report
output_file = 'all_138_files_updated_report.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Total files processed: {report['summary']['overall']['files_processed']}")
print(f"Total items extracted: {report['summary']['overall']['total_items']}")
print(f"Total amount: {report['summary']['overall']['total_amount']:,.2f} THB")

print("\nBy Platform:")
for platform, data in report['summary']['by_platform'].items():
    print(f"\n{platform}:")
    print(f"  Files: {data['files']}")
    print(f"  Items: {data['total_items']}")
    print(f"  Total: {data['total_amount']:,.2f} THB")
    print(f"  Avg items/file: {data['average_items_per_file']}")

print(f"\nReport saved to: {output_file}")

# Also save a summary report
summary_file = 'parser_accuracy_summary.json'
summary = {
    'generated_at': datetime.now().isoformat(),
    'expected_totals': {
        'TikTok': 2440716.88,
        'Facebook': 12831605.92,
        'Google': 2362684.79
    },
    'actual_totals': {
        'TikTok': report['summary']['by_platform'].get('TikTok', {}).get('total_amount', 0),
        'Facebook': report['summary']['by_platform'].get('Facebook', {}).get('total_amount', 0),
        'Google': report['summary']['by_platform'].get('Google', {}).get('total_amount', 0)
    },
    'accuracy': {},
    'items_per_file': {
        'TikTok': report['summary']['by_platform'].get('TikTok', {}).get('average_items_per_file', 0),
        'Facebook': report['summary']['by_platform'].get('Facebook', {}).get('average_items_per_file', 0),
        'Google': report['summary']['by_platform'].get('Google', {}).get('average_items_per_file', 0)
    }
}

# Calculate accuracy
for platform in ['TikTok', 'Facebook', 'Google']:
    expected = summary['expected_totals'][platform]
    actual = summary['actual_totals'][platform]
    diff = abs(actual - expected)
    summary['accuracy'][platform] = {
        'difference': diff,
        'percentage': round((1 - diff/expected) * 100, 2) if expected > 0 else 0,
        'status': 'CORRECT' if diff < 10 else 'INCORRECT'
    }

with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"Summary saved to: {summary_file}")