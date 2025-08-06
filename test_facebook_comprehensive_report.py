"""
Generate comprehensive Facebook invoice test report
Creates detailed analysis of all 59 Facebook invoices
"""

import os
import json
from datetime import datetime
import fitz  # PyMuPDF
from backend.app import parse_facebook_text

def test_all_facebook_invoices():
    """Process all Facebook invoices and generate comprehensive report"""
    invoice_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    # Find all Facebook invoices
    facebook_files = []
    for filename in os.listdir(invoice_dir):
        if filename.endswith('.pdf') and (filename.startswith('246') or filename.startswith('247')):
            facebook_files.append(filename)
    
    facebook_files.sort()
    print(f"Found {len(facebook_files)} Facebook invoice files")
    
    # Process each file
    all_results = []
    summary = {
        'total_files': len(facebook_files),
        'ap_files': 0,
        'non_ap_files': 0,
        'total_line_items': 0,
        'total_amount': 0.0,
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'files': []
    }
    
    for idx, filename in enumerate(facebook_files, 1):
        print(f"\n[{idx:3}/{len(facebook_files)}] Processing {filename}...")
        
        try:
            # Extract text from PDF
            filepath = os.path.join(invoice_dir, filename)
            text_content = ""
            
            with fitz.open(filepath) as doc:
                text_content = '\n'.join([page.get_text() for page in doc])
            
            # Parse with Facebook parser
            records = parse_facebook_text(text_content, filename, "Facebook")
            
            # Analyze results
            invoice_type = records[0].get('invoice_type', 'Unknown') if records else 'Unknown'
            is_ap = invoice_type == 'AP'
            
            if is_ap:
                summary['ap_files'] += 1
            else:
                summary['non_ap_files'] += 1
            
            # Calculate file total
            file_total = 0.0
            file_records = []
            
            for record in records:
                amount = record.get('total', 0.0) or 0.0
                file_total += amount
                summary['total_line_items'] += 1
                
                # Create detailed record
                detailed_record = {
                    'line_number': record.get('line_number'),
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
            
            # For Non-AP invoices, use invoice total from first record
            if not is_ap and records:
                # Look for invoice_total field
                if 'invoice_total' in records[0] and records[0]['invoice_total']:
                    file_total = records[0]['invoice_total']
            
            summary['total_amount'] += file_total
            
            # File summary
            file_summary = {
                'filename': filename,
                'invoice_type': invoice_type,
                'total_amount': file_total,
                'line_items_count': len(records),
                'line_items': file_records
            }
            
            summary['files'].append(file_summary)
            all_results.append(file_summary)
            
            print(f"  Type: {invoice_type}")
            print(f"  Total: {file_total:,.2f} THB")
            print(f"  Line items: {len(records)}")
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            summary['files'].append({
                'filename': filename,
                'error': str(e)
            })
    
    # Generate reports
    print("\n" + "="*80)
    print("GENERATING REPORTS...")
    
    # JSON report
    json_report_path = r"C:\Users\peerapong\invoice-reader-app\facebook_invoice_comprehensive_report.json"
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"JSON report saved: {json_report_path}")
    
    # Text report
    txt_report_path = r"C:\Users\peerapong\invoice-reader-app\facebook_invoice_comprehensive_report.txt"
    with open(txt_report_path, 'w', encoding='utf-8') as f:
        f.write("COMPREHENSIVE FACEBOOK INVOICE ANALYSIS REPORT\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Report Generated: {summary['processing_date']}\n")
        f.write(f"Total Files Processed: {summary['total_files']}\n")
        f.write(f"AP Invoices: {summary['ap_files']}\n")
        f.write(f"Non-AP Invoices: {summary['non_ap_files']}\n")
        f.write(f"Total Line Items: {summary['total_line_items']}\n")
        f.write(f"Total Amount: {summary['total_amount']:,.2f} THB\n")
        f.write("\n" + "=" * 100 + "\n\n")
        
        # Detailed file-by-file breakdown
        f.write("DETAILED FILE-BY-FILE BREAKDOWN\n")
        f.write("=" * 100 + "\n\n")
        
        for file_data in summary['files']:
            if 'error' in file_data:
                f.write(f"FILE: {file_data['filename']}\n")
                f.write(f"ERROR: {file_data['error']}\n")
                f.write("-" * 100 + "\n\n")
                continue
            
            f.write(f"FILE: {file_data['filename']}\n")
            f.write(f"Invoice Type: {file_data['invoice_type']}\n")
            f.write(f"Total Amount: {file_data['total_amount']:,.2f} THB\n")
            f.write(f"Line Items: {file_data['line_items_count']}\n")
            f.write("\n")
            
            if file_data['line_items']:
                f.write("LINE ITEM DETAILS:\n")
                for item in file_data['line_items']:
                    f.write(f"  Line {item.get('line_number', 'N/A')}:\n")
                    if item.get('agency'):
                        f.write(f"    Agency: {item['agency']}\n")
                    if item.get('project_id'):
                        f.write(f"    Project ID: {item['project_id']}\n")
                    if item.get('project_name'):
                        f.write(f"    Project Name: {item['project_name']}\n")
                    if item.get('campaign_id'):
                        f.write(f"    Campaign ID: {item['campaign_id']}\n")
                    if item.get('objective'):
                        f.write(f"    Objective: {item['objective']}\n")
                    if item.get('period'):
                        f.write(f"    Period: {item['period']}\n")
                    if item.get('description'):
                        f.write(f"    Description: {item['description'][:100]}{'...' if len(item.get('description', '')) > 100 else ''}\n")
                    f.write(f"    Amount: {item['amount']:,.2f} THB\n")
                    f.write("\n")
            
            f.write("-" * 100 + "\n\n")
        
        # Summary statistics
        f.write("SUMMARY STATISTICS\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Average per file: {summary['total_amount'] / summary['total_files']:,.2f} THB\n")
        if summary['total_line_items'] > 0:
            f.write(f"Average per line item: {summary['total_amount'] / summary['total_line_items']:,.2f} THB\n")
        
        # AP vs Non-AP breakdown
        ap_total = sum(f['total_amount'] for f in summary['files'] if f.get('invoice_type') == 'AP')
        non_ap_total = sum(f['total_amount'] for f in summary['files'] if f.get('invoice_type') == 'Non-AP')
        
        f.write(f"\nAP Invoices Total: {ap_total:,.2f} THB ({(ap_total/summary['total_amount']*100):.1f}%)\n")
        f.write(f"Non-AP Invoices Total: {non_ap_total:,.2f} THB ({(non_ap_total/summary['total_amount']*100):.1f}%)\n")
    
    print(f"Text report saved: {txt_report_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total Files: {summary['total_files']}")
    print(f"AP Invoices: {summary['ap_files']}")
    print(f"Non-AP Invoices: {summary['non_ap_files']}")
    print(f"Total Line Items: {summary['total_line_items']}")
    print(f"Total Amount: {summary['total_amount']:,.2f} THB")
    print(f"Expected Total: 12,831,605.92 THB")
    print(f"Difference: {summary['total_amount'] - 12831605.92:,.2f} THB")

if __name__ == "__main__":
    test_all_facebook_invoices()