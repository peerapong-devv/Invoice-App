"""
Generate comprehensive Google invoice test report
Creates detailed analysis of all 57 Google invoices
"""

import os
import json
from datetime import datetime
import fitz  # PyMuPDF
import sys
sys.path.append('backend')
from app import parse_google_text

def test_all_google_invoices():
    """Process all Google invoices and generate comprehensive report"""
    invoice_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    # Find all Google invoices (5xxxxxxxx files)
    google_files = []
    for filename in os.listdir(invoice_dir):
        if filename.endswith('.pdf') and filename[0].isdigit() and len(filename.split('.')[0]) >= 10:
            # Check if it starts with 5 (Google invoice pattern)
            if filename.startswith('5'):
                google_files.append(filename)
    
    google_files.sort()
    print(f"Found {len(google_files)} Google invoice files")
    
    # Process each file
    all_results = []
    summary = {
        'total_files': len(google_files),
        'successful_files': 0,
        'error_files': 0,
        'total_line_items': 0,
        'total_amount': 0.0,
        'campaign_items': 0,
        'refund_items': 0,
        'fee_items': 0,
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'files': []
    }
    
    for idx, filename in enumerate(google_files, 1):
        print(f"\n[{idx:3}/{len(google_files)}] Processing {filename}...")
        
        try:
            # Extract text from PDF
            filepath = os.path.join(invoice_dir, filename)
            text_content = ""
            
            with fitz.open(filepath) as doc:
                text_content = '\n'.join([page.get_text() for page in doc])
            
            # Parse with Google parser
            records = parse_google_text(text_content, filename, "Google")
            
            if not records:
                print(f"  WARNING: No records found")
                summary['files'].append({
                    'filename': filename,
                    'warning': 'No records found'
                })
                continue
            
            # Analyze results
            file_total = 0.0
            file_records = []
            campaign_count = 0
            refund_count = 0
            fee_count = 0
            
            for record in records:
                amount = record.get('total', 0.0) or 0.0
                file_total += amount
                summary['total_line_items'] += 1
                
                # Count item types
                item_type = record.get('item_type', 'Unknown')
                if item_type == 'Campaign':
                    campaign_count += 1
                    summary['campaign_items'] += 1
                elif item_type == 'Refund':
                    refund_count += 1
                    summary['refund_items'] += 1
                elif item_type == 'Fee':
                    fee_count += 1
                    summary['fee_items'] += 1
                
                # Create detailed record
                detailed_record = {
                    'line_number': record.get('line_number'),
                    'item_type': item_type,
                    'agency': record.get('agency'),
                    'project_id': record.get('project_id'),
                    'project_name': record.get('project_name'),
                    'campaign_id': record.get('campaign_id'),
                    'objective': record.get('objective'),
                    'period': record.get('period'),
                    'description': record.get('description'),
                    'amount': amount
                }
                file_records.append(detailed_record)
            
            summary['total_amount'] += file_total
            summary['successful_files'] += 1
            
            # File summary
            file_summary = {
                'filename': filename,
                'total_amount': file_total,
                'line_items_count': len(file_records),
                'campaign_items': campaign_count,
                'refund_items': refund_count,
                'fee_items': fee_count,
                'line_items': file_records
            }
            
            summary['files'].append(file_summary)
            
            print(f"  Total: {file_total:,.2f} THB")
            print(f"  Line items: {len(file_records)} (C:{campaign_count}, R:{refund_count}, F:{fee_count})")
            
            # Show sample
            if file_records:
                sample = file_records[0]
                if sample.get('description'):
                    desc = sample.get('description', '')[:80]
                    print(f"  Sample: {desc}...")
                    
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            summary['error_files'] += 1
            summary['files'].append({
                'filename': filename,
                'error': str(e)
            })
    
    # Generate reports
    print("\n" + "="*80)
    print("GENERATING REPORTS...")
    
    # Save JSON report
    json_report_path = r"C:\Users\peerapong\invoice-reader-app\google_invoice_comprehensive_report.json"
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"JSON report saved: {json_report_path}")
    
    # Save text report
    txt_report_path = r"C:\Users\peerapong\invoice-reader-app\google_invoice_comprehensive_report.txt"
    with open(txt_report_path, 'w', encoding='utf-8') as f:
        f.write("COMPREHENSIVE GOOGLE INVOICE ANALYSIS REPORT\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Report Generated: {summary['processing_date']}\n")
        f.write(f"Total Files Processed: {summary['total_files']}\n")
        f.write(f"Successful Files: {summary['successful_files']}\n")
        f.write(f"Error Files: {summary['error_files']}\n")
        f.write(f"Total Line Items: {summary['total_line_items']}\n")
        f.write(f"Campaign Items: {summary['campaign_items']}\n")
        f.write(f"Refund Items: {summary['refund_items']}\n")
        f.write(f"Fee Items: {summary['fee_items']}\n")
        f.write(f"Total Amount: {summary['total_amount']:,.2f} THB\n\n")
        f.write("=" * 100 + "\n\n")
        
        # Sample Google descriptions
        f.write("SAMPLE GOOGLE INVOICE DESCRIPTIONS:\n")
        f.write("-" * 50 + "\n")
        sample_count = 0
        for file_data in summary['files']:
            if sample_count < 10 and 'line_items' in file_data:
                for item in file_data.get('line_items', []):
                    desc = item.get('description', '')
                    if desc and len(desc) > 20:
                        f.write(f"{file_data['filename']}: {desc[:100]}...\n")
                        sample_count += 1
                        break
        
        # File breakdown by type
        f.write(f"\nDETAILED FILE BREAKDOWN\n")
        f.write("-" * 50 + "\n")
        
        campaign_total = 0
        refund_total = 0
        fee_total = 0
        
        for file_data in summary['files']:
            if 'error' not in file_data and 'warning' not in file_data:
                f.write(f"\n{file_data['filename']}\n")
                f.write(f"  Amount: {file_data['total_amount']:,.2f} THB\n")
                f.write(f"  Line Items: {file_data['line_items_count']}\n")
                f.write(f"  Types: C:{file_data['campaign_items']} R:{file_data['refund_items']} F:{file_data['fee_items']}\n")
                
                # Calculate totals by type
                for item in file_data.get('line_items', []):
                    item_type = item.get('item_type', 'Unknown')
                    amount = item.get('amount', 0)
                    if item_type == 'Campaign':
                        campaign_total += amount
                    elif item_type == 'Refund':
                        refund_total += amount
                    elif item_type == 'Fee':
                        fee_total += amount
        
        f.write(f"\n" + "=" * 50 + "\n")
        f.write(f"Campaign Total: {campaign_total:,.2f} THB ({summary['campaign_items']} items)\n")
        f.write(f"Refund Total: {refund_total:,.2f} THB ({summary['refund_items']} items)\n")
        f.write(f"Fee Total: {fee_total:,.2f} THB ({summary['fee_items']} items)\n")
        f.write(f"Grand Total: {summary['total_amount']:,.2f} THB\n")
        
        # Error summary
        if summary['error_files'] > 0:
            f.write(f"\nERROR FILES ({summary['error_files']}):\n")
            f.write("-" * 30 + "\n")
            for file_data in summary['files']:
                if 'error' in file_data:
                    f.write(f"{file_data['filename']}: {file_data['error']}\n")
    
    print(f"Text report saved: {txt_report_path}")
    
    # Print final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total Files: {summary['total_files']}")
    print(f"Successful: {summary['successful_files']}")
    print(f"Errors: {summary['error_files']}")
    print(f"Total Line Items: {summary['total_line_items']}")
    print(f"Campaign Items: {summary['campaign_items']}")
    print(f"Refund Items: {summary['refund_items']}")
    print(f"Fee Items: {summary['fee_items']}")
    print(f"Total Amount: {summary['total_amount']:,.2f} THB")

if __name__ == "__main__":
    test_all_google_invoices()