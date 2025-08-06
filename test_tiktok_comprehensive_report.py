"""
Generate comprehensive TikTok invoice test report
Creates detailed analysis of all 22 TikTok invoices
"""

import os
import json
from datetime import datetime
import fitz  # PyMuPDF
import sys
sys.path.append('backend')
from app import parse_tiktok_text

def test_all_tiktok_invoices():
    """Process all TikTok invoices and generate comprehensive report"""
    invoice_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    # Find all TikTok invoices (THTT files)
    tiktok_files = []
    for filename in os.listdir(invoice_dir):
        if filename.endswith('.pdf') and filename.startswith('THTT'):
            tiktok_files.append(filename)
    
    tiktok_files.sort()
    print(f"Found {len(tiktok_files)} TikTok invoice files")
    
    # Process each file
    all_results = []
    summary = {
        'total_files': len(tiktok_files),
        'ap_files': 0,
        'non_ap_files': 0,
        'total_line_items': 0,
        'total_amount': 0.0,
        'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'files': []
    }
    
    for idx, filename in enumerate(tiktok_files, 1):
        print(f"\n[{idx:3}/{len(tiktok_files)}] Processing {filename}...")
        
        try:
            # Extract text from PDF
            filepath = os.path.join(invoice_dir, filename)
            text_content = ""
            
            with fitz.open(filepath) as doc:
                text_content = '\n'.join([page.get_text() for page in doc])
            
            # Parse with TikTok parser
            records = parse_tiktok_text(text_content, filename, "TikTok")
            
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
            
            summary['total_amount'] += file_total
            
            # File summary
            file_summary = {
                'filename': filename,
                'invoice_type': invoice_type,
                'total_amount': file_total,
                'line_items_count': len(file_records),
                'line_items': file_records
            }
            
            summary['files'].append(file_summary)
            
            print(f"  Type: {invoice_type}")
            print(f"  Total: {file_total:,.2f} THB")
            print(f"  Line items: {len(file_records)}")
            
            # Show sample
            if file_records:
                sample = file_records[0]
                if sample.get('description'):
                    desc = sample.get('description', '')[:100]
                    print(f"  Sample: {desc}...")
                    
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            summary['files'].append({
                'filename': filename,
                'error': str(e)
            })
    
    # Generate reports
    print("\n" + "="*80)
    print("GENERATING REPORTS...")
    
    # Save JSON report
    json_report_path = r"C:\Users\peerapong\invoice-reader-app\tiktok_invoice_comprehensive_report.json"
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"JSON report saved: {json_report_path}")
    
    # Save text report
    txt_report_path = r"C:\Users\peerapong\invoice-reader-app\tiktok_invoice_comprehensive_report.txt"
    with open(txt_report_path, 'w', encoding='utf-8') as f:
        f.write("COMPREHENSIVE TIKTOK INVOICE ANALYSIS REPORT\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Report Generated: {summary['processing_date']}\n")
        f.write(f"Total Files Processed: {summary['total_files']}\n")
        f.write(f"AP Invoices: {summary['ap_files']}\n")
        f.write(f"Non-AP Invoices: {summary['non_ap_files']}\n")
        f.write(f"Total Line Items: {summary['total_line_items']}\n")
        f.write(f"Total Amount: {summary['total_amount']:,.2f} THB\n\n")
        f.write("=" * 100 + "\n\n")
        
        # Sample descriptions
        f.write("SAMPLE TIKTOK INVOICE DESCRIPTIONS:\n")
        f.write("-" * 50 + "\n")
        sample_count = 0
        for file_data in summary['files']:
            if sample_count < 5:
                for item in file_data.get('line_items', []):
                    desc = item.get('description', '')
                    if desc and len(desc) > 20:
                        f.write(f"{file_data['filename']}: {desc[:100]}...\n")
                        sample_count += 1
                        break
        
        # File breakdown
        f.write(f"\nDETAILED FILE BREAKDOWN\n")
        f.write("-" * 50 + "\n")
        
        ap_total = 0
        non_ap_total = 0
        
        for file_data in summary['files']:
            if 'error' not in file_data:
                f.write(f"\n{file_data['filename']} ({file_data['invoice_type']})\n")
                f.write(f"  Amount: {file_data['total_amount']:,.2f} THB\n")
                f.write(f"  Line Items: {file_data['line_items_count']}\n")
                
                if file_data['invoice_type'] == 'AP':
                    ap_total += file_data['total_amount']
                else:
                    non_ap_total += file_data['total_amount']
        
        f.write(f"\n" + "=" * 50 + "\n")
        f.write(f"AP Total: {ap_total:,.2f} THB ({summary['ap_files']} files)\n")
        f.write(f"Non-AP Total: {non_ap_total:,.2f} THB ({summary['non_ap_files']} files)\n")
        f.write(f"Grand Total: {summary['total_amount']:,.2f} THB\n")
    
    print(f"Text report saved: {txt_report_path}")
    
    # Print final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total Files: {summary['total_files']}")
    print(f"AP Invoices: {summary['ap_files']}")
    print(f"Non-AP Invoices: {summary['non_ap_files']}")
    print(f"Total Line Items: {summary['total_line_items']}")
    print(f"Total Amount: {summary['total_amount']:,.2f} THB")

if __name__ == "__main__":
    test_all_tiktok_invoices()