#!/usr/bin/env python3
"""
Generate comprehensive report for all platforms showing extraction quality
"""

import os
import json
import fitz
from datetime import datetime
from collections import defaultdict

# Import all parsers
from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed
from truly_fixed_facebook_parser import parse_facebook_invoice_truly_fixed
from google_parser_complete import parse_google_invoice_complete

def process_all_invoices():
    """Process all invoices and generate comprehensive report"""
    
    invoice_dir = "../Invoice for testing"
    if not os.path.exists(invoice_dir):
        print(f"Error: Invoice directory '{invoice_dir}' not found")
        return
    
    # Categorize files by platform
    tiktok_files = []
    facebook_files = []
    google_files = []
    
    for filename in os.listdir(invoice_dir):
        if filename.endswith('.pdf'):
            if filename.startswith('THTT'):
                tiktok_files.append(filename)
            elif filename.startswith('246') or filename.startswith('247'):
                facebook_files.append(filename)
            elif filename.startswith('5'):
                google_files.append(filename)
    
    # Process each platform
    all_results = {
        'tiktok': process_platform_files(tiktok_files, invoice_dir, 'tiktok'),
        'facebook': process_platform_files(facebook_files, invoice_dir, 'facebook'),
        'google': process_platform_files(google_files, invoice_dir, 'google')
    }
    
    # Generate comprehensive report
    generate_report(all_results)
    
    # Save detailed results
    save_json_reports(all_results)

def process_platform_files(files, invoice_dir, platform):
    """Process all files for a specific platform"""
    
    results = {
        'files': [],
        'total_amount': 0,
        'total_items': 0,
        'ap_files': 0,
        'non_ap_files': 0,
        'errors': []
    }
    
    for filename in sorted(files):
        file_path = os.path.join(invoice_dir, filename)
        
        try:
            # Extract text
            with fitz.open(file_path) as doc:
                text_content = ""
                for page in doc:
                    text_content += page.get_text()
            
            # Parse based on platform
            if platform == 'tiktok':
                records = parse_tiktok_invoice_detailed(text_content, filename)
            elif platform == 'facebook':
                records = parse_facebook_invoice_truly_fixed(text_content, filename)
            elif platform == 'google':
                records = parse_google_invoice_complete(text_content, filename)
            else:
                records = []
            
            # Calculate file totals
            file_total = sum(r.get('total', r.get('amount', 0)) for r in records)
            
            # Determine invoice type
            invoice_type = records[0].get('invoice_type', 'Unknown') if records else 'Unknown'
            
            # Count AP fields completeness for AP invoices
            ap_completeness = 0
            if invoice_type == 'AP':
                ap_completeness = sum(1 for r in records if r.get('campaign_id') != 'Unknown' and r.get('campaign_id'))
            
            file_result = {
                'filename': filename,
                'invoice_type': invoice_type,
                'item_count': len(records),
                'total_amount': file_total,
                'ap_fields_complete': ap_completeness,
                'success': True
            }
            
            results['files'].append(file_result)
            results['total_amount'] += file_total
            results['total_items'] += len(records)
            
            if invoice_type == 'AP':
                results['ap_files'] += 1
            else:
                results['non_ap_files'] += 1
                
        except Exception as e:
            results['errors'].append({
                'filename': filename,
                'error': str(e)
            })
            results['files'].append({
                'filename': filename,
                'invoice_type': 'Error',
                'item_count': 0,
                'total_amount': 0,
                'success': False,
                'error': str(e)
            })
    
    return results

def generate_report(all_results):
    """Generate comprehensive text report"""
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("COMPREHENSIVE INVOICE EXTRACTION REPORT")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Summary statistics
    report_lines.append("OVERALL SUMMARY")
    report_lines.append("-" * 40)
    
    total_files = sum(len(r['files']) for r in all_results.values())
    total_amount = sum(r['total_amount'] for r in all_results.values())
    total_items = sum(r['total_items'] for r in all_results.values())
    
    report_lines.append(f"Total files processed: {total_files}")
    report_lines.append(f"Total amount extracted: {total_amount:,.2f} THB")
    report_lines.append(f"Total line items extracted: {total_items:,}")
    report_lines.append("")
    
    # Platform-specific summaries
    for platform in ['tiktok', 'facebook', 'google']:
        results = all_results[platform]
        
        report_lines.append(f"\n{platform.upper()} PLATFORM SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Files processed: {len(results['files'])}")
        report_lines.append(f"Total amount: {results['total_amount']:,.2f} THB")
        report_lines.append(f"Total items: {results['total_items']:,}")
        report_lines.append(f"AP invoices: {results['ap_files']}")
        report_lines.append(f"Non-AP invoices: {results['non_ap_files']}")
        
        if results['errors']:
            report_lines.append(f"Errors: {len(results['errors'])}")
        
        # Average items per invoice
        if results['files']:
            avg_items = results['total_items'] / len(results['files'])
            report_lines.append(f"Average items per invoice: {avg_items:.1f}")
        
        # AP field completeness for AP invoices
        ap_files_with_data = [f for f in results['files'] if f['invoice_type'] == 'AP' and f['ap_fields_complete'] > 0]
        if ap_files_with_data:
            total_ap_complete = sum(f['ap_fields_complete'] for f in ap_files_with_data)
            total_ap_items = sum(f['item_count'] for f in ap_files_with_data)
            if total_ap_items > 0:
                ap_completeness = (total_ap_complete / total_ap_items) * 100
                report_lines.append(f"AP field completeness: {ap_completeness:.1f}%")
    
    # Detailed file listing
    report_lines.append("\n\nDETAILED FILE RESULTS")
    report_lines.append("=" * 80)
    
    for platform in ['tiktok', 'facebook', 'google']:
        results = all_results[platform]
        
        report_lines.append(f"\n{platform.upper()} FILES:")
        report_lines.append("-" * 80)
        report_lines.append(f"{'Filename':<25} {'Type':<8} {'Items':<8} {'Amount':<15} {'Status'}")
        report_lines.append("-" * 80)
        
        for file_result in sorted(results['files'], key=lambda x: x['filename']):
            status = "OK" if file_result['success'] else "ERROR"
            report_lines.append(
                f"{file_result['filename']:<25} "
                f"{file_result['invoice_type']:<8} "
                f"{file_result['item_count']:<8} "
                f"{file_result['total_amount']:>14,.2f} "
                f"{status}"
            )
    
    # Known issues and comparison
    report_lines.append("\n\nEXPECTED VS ACTUAL TOTALS")
    report_lines.append("-" * 40)
    
    # Expected totals from user data
    expected_totals = {
        'tiktok': 10196493.21,
        'facebook': 12818874.17,
        'google': 2362684.79
    }
    
    for platform in ['tiktok', 'facebook', 'google']:
        actual = all_results[platform]['total_amount']
        expected = expected_totals[platform]
        difference = actual - expected
        accuracy = (actual / expected * 100) if expected > 0 else 0
        
        report_lines.append(f"\n{platform.upper()}:")
        report_lines.append(f"  Expected: {expected:,.2f} THB")
        report_lines.append(f"  Actual:   {actual:,.2f} THB")
        report_lines.append(f"  Difference: {difference:,.2f} THB ({accuracy:.1f}% accuracy)")
    
    # Save report
    report_content = "\n".join(report_lines)
    
    with open("comprehensive_extraction_report.txt", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(report_content)

def save_json_reports(all_results):
    """Save detailed JSON reports for each platform"""
    
    # Save individual platform reports
    for platform in ['tiktok', 'facebook', 'google']:
        results = all_results[platform]
        
        # Create detailed report structure
        report = {
            'platform': platform,
            'summary': {
                'total_files': len(results['files']),
                'total_amount': results['total_amount'],
                'total_items': results['total_items'],
                'ap_files': results['ap_files'],
                'non_ap_files': results['non_ap_files'],
                'error_count': len(results['errors'])
            },
            'files': results['files'],
            'errors': results['errors']
        }
        
        filename = f"{platform}_extraction_report.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {filename}")
    
    # Save combined report
    with open("all_platforms_extraction_report.json", 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print("Saved all_platforms_extraction_report.json")

if __name__ == "__main__":
    process_all_invoices()