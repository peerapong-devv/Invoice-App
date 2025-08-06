#!/usr/bin/env python3
"""
Comprehensive test of updated backend against ALL Facebook AP invoices
"""
import os
import sys
sys.path.append('backend')

import fitz  # PyMuPDF
from app import process_invoice_file

def test_all_facebook_ap_invoices():
    """Test the updated backend code against all Facebook AP invoices"""
    
    # List of all Facebook AP invoices
    ap_invoices = [
        '246543739.pdf',
        '246546622.pdf', 
        '246578231.pdf',
        '246579423.pdf',
        '246727587.pdf',
        '246738919.pdf',
        '246774670.pdf',
        '246791975.pdf',
        '246865374.pdf'
    ]
    
    test_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    print("COMPREHENSIVE FACEBOOK AP INVOICE TEST")
    print("=" * 60)
    print(f"Testing {len(ap_invoices)} Facebook AP invoices with updated backend code")
    print("=" * 60)
    
    results = {}
    total_records = 0
    total_amount = 0
    
    for invoice_file in ap_invoices:
        filepath = os.path.join(test_dir, invoice_file)
        
        if not os.path.exists(filepath):
            print(f"ERROR: File not found: {invoice_file}")
            continue
        
        print(f"\nProcessing: {invoice_file}")
        
        try:
            # Use the updated backend processing
            records = process_invoice_file(filepath, invoice_file)
            
            if not records:
                print(f"WARNING: No records returned for {invoice_file}")
                continue
            
            # Calculate stats for this invoice
            ap_records = [r for r in records if r.get('invoice_type') == 'AP']
            non_ap_records = [r for r in records if r.get('invoice_type') == 'Non-AP']
            
            invoice_total = sum(r['total'] for r in records if r['total'] is not None)
            
            results[invoice_file] = {
                'total_records': len(records),
                'ap_records': len(ap_records),
                'non_ap_records': len(non_ap_records),
                'invoice_total': invoice_total,
                'records': records
            }
            
            total_records += len(records)
            total_amount += invoice_total
            
            print(f"   Records: {len(records)} (AP: {len(ap_records)}, Non-AP: {len(non_ap_records)})")
            print(f"   Total: {invoice_total:,.2f} THB")
            
            # Show sample record details
            if ap_records:
                sample = ap_records[0]
                print(f"   Sample: Project {sample.get('project_id', 'N/A')} | Campaign {sample.get('campaign_id', 'N/A')} | Objective {sample.get('objective', 'N/A')}")
                
        except Exception as e:
            print(f"ERROR processing {invoice_file}: {e}")
    
    # Summary Report
    print(f"\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    print(f"Total invoices processed: {len(results)}")
    print(f"Total records extracted: {total_records}")
    print(f"Total amount: {total_amount:,.2f} THB")
    
    # Detailed breakdown
    print(f"\nDETAILED BREAKDOWN:")
    print("-" * 40)
    for invoice_file, data in results.items():
        print(f"{invoice_file:15s}: {data['total_records']:3d} records | {data['invoice_total']:>12,.2f} THB")
    
    # Validate against known totals
    print(f"\nVALIDATION AGAINST KNOWN TOTALS:")
    print("-" * 40)
    
    known_totals = {
        '246791975.pdf': 1417663.24  # As stated by user
    }
    
    validation_passed = 0
    for invoice_file, expected_total in known_totals.items():
        if invoice_file in results:
            actual_total = results[invoice_file]['invoice_total']
            status = "PASS" if abs(actual_total - expected_total) < 0.01 else "FAIL"
            print(f"{invoice_file}: Expected: {expected_total:,.2f} | Actual: {actual_total:,.2f} | {status}")
            if status == "PASS":
                validation_passed += 1
        else:
            print(f"{invoice_file}: Not processed")
    
    print(f"\nValidation Results: {validation_passed}/{len(known_totals)} invoices passed")
    
    # Top projects by spending
    print(f"\nTOP PROJECTS BY SPENDING:")
    print("-" * 40)
    project_totals = {}
    for invoice_data in results.values():
        for record in invoice_data['records']:
            if record.get('project_id') and record.get('total'):
                pid = record['project_id']
                project_totals[pid] = project_totals.get(pid, 0) + record['total']
    
    sorted_projects = sorted(project_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    for project_id, total in sorted_projects:
        print(f"Project {project_id}: {total:,.2f} THB")
    
    return results

def compare_with_pdf_source(invoice_file, results):
    """Compare extracted results with original PDF to verify accuracy"""
    
    filepath = os.path.join(r"C:\Users\peerapong\invoice-reader-app\Invoice for testing", invoice_file)
    
    if not os.path.exists(filepath):
        return False
    
    # Extract original text for comparison
    doc = fitz.open(filepath)
    full_text = "\n".join(page.get_text() for page in doc)
    doc.close()
    
    # Count [ST] markers in original
    st_count_original = full_text.count('[ST]')
    
    # Count [ST] records extracted
    ap_records = [r for r in results if r.get('invoice_type') == 'AP']
    st_count_extracted = len(ap_records)
    
    print(f"\nACCURACY CHECK - {invoice_file}")
    print(f"   Original [ST] markers: {st_count_original}")
    print(f"   Extracted AP records: {st_count_extracted}")
    print(f"   Match: {'YES' if st_count_original == st_count_extracted else 'NO'}")
    
    return st_count_original == st_count_extracted

if __name__ == "__main__":
    results = test_all_facebook_ap_invoices()
    
    # Test accuracy for key invoice
    if '246791975.pdf' in results:
        print(f"\nACCURACY VERIFICATION:")
        print("=" * 30)
        invoice_data = results['246791975.pdf']
        compare_with_pdf_source('246791975.pdf', invoice_data['records'])