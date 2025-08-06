import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import process_invoice_file
import json
import fitz  # PyMuPDF
import re

def identify_invoice_type(pdf_path):
    """Identify if invoice is Google and if it's AP or Non-AP"""
    try:
        with fitz.open(pdf_path) as doc:
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"
        
        # Clean zero-width spaces
        full_text = full_text.replace('\u200b', '')
        
        # Check if it's a Google invoice
        is_google = ("google" in full_text.lower() and "ads" in full_text.lower()) or \
                   "Google Asia Pacific" in full_text
        
        # Check if it's AP - look for various pk| patterns
        is_ap = False
        
        # Direct pattern
        if "pk|" in full_text:
            is_ap = True
        
        # Character-split pattern (p\nk\n|)
        elif re.search(r'p\s*\n\s*k\s*\n\s*\|', full_text):
            is_ap = True
        
        # Check for reconstructed pattern
        lines = full_text.split('\n')
        for i in range(len(lines) - 2):
            if lines[i].strip() == 'p' and lines[i+1].strip() == 'k' and lines[i+2].strip() == '|':
                is_ap = True
                break
        
        return is_google, is_ap, full_text
    except Exception as e:
        return False, False, str(e)

def test_all_google_invoices():
    """Test all invoices in the folder and identify Google AP vs Non-AP"""
    
    invoice_folder = "Invoice for testing"
    all_files = os.listdir(invoice_folder)
    pdf_files = [f for f in all_files if f.endswith('.pdf')]
    
    print(f"Found {len(pdf_files)} PDF files in {invoice_folder}\n")
    
    google_ap_files = []
    google_non_ap_files = []
    non_google_files = []
    
    # First pass: Identify invoice types
    print("=== IDENTIFYING INVOICE TYPES ===\n")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(invoice_folder, pdf_file)
        is_google, is_ap, _ = identify_invoice_type(pdf_path)
        
        if is_google:
            if is_ap:
                google_ap_files.append(pdf_file)
                print(f"[AP] {pdf_file}")
            else:
                google_non_ap_files.append(pdf_file)
                print(f"[Non-AP] {pdf_file}")
        else:
            non_google_files.append(pdf_file)
            # Don't print non-Google files to reduce output
    
    print(f"\n=== SUMMARY ===")
    print(f"Google AP invoices: {len(google_ap_files)}")
    print(f"Google Non-AP invoices: {len(google_non_ap_files)}")
    print(f"Non-Google invoices: {len(non_google_files)}")
    print(f"Total files: {len(pdf_files)}")
    
    # Process Google AP invoices
    print(f"\n=== PROCESSING GOOGLE AP INVOICES ({len(google_ap_files)} files) ===\n")
    
    all_ap_results = []
    ap_summary = []
    
    for idx, pdf_file in enumerate(google_ap_files, 1):
        print(f"[{idx}/{len(google_ap_files)}] {pdf_file}")
        
        pdf_path = os.path.join(invoice_folder, pdf_file)
        
        # Create temp upload folder
        if not os.path.exists('backend/uploads'):
            os.makedirs('backend/uploads')
        
        # Copy file to uploads folder
        import shutil
        upload_path = os.path.join('backend/uploads', pdf_file)
        shutil.copy(pdf_path, upload_path)
        
        try:
            records = process_invoice_file(upload_path, pdf_file)
            
            print(f"  -> {len(records)} line items")
            
            # Collect summary info
            total_amount = sum(r['total'] for r in records if r['total'])
            ap_summary.append({
                'file': pdf_file,
                'line_items': len(records),
                'total_amount': total_amount
            })
            
            all_ap_results.extend(records)
            
        except Exception as e:
            print(f"  -> ERROR: {str(e)[:50]}...")
            ap_summary.append({
                'file': pdf_file,
                'line_items': 0,
                'total_amount': 0,
                'error': str(e)
            })
    
    # Process Google Non-AP invoices
    print(f"\n=== PROCESSING GOOGLE NON-AP INVOICES ({len(google_non_ap_files)} files) ===\n")
    
    all_non_ap_results = []
    non_ap_summary = []
    
    for idx, pdf_file in enumerate(google_non_ap_files, 1):
        print(f"[{idx}/{len(google_non_ap_files)}] {pdf_file}")
        
        pdf_path = os.path.join(invoice_folder, pdf_file)
        upload_path = os.path.join('backend/uploads', pdf_file)
        shutil.copy(pdf_path, upload_path)
        
        try:
            records = process_invoice_file(upload_path, pdf_file)
            
            print(f"  -> {len(records)} line items")
            
            # Collect summary info
            total_amount = sum(r['total'] for r in records if r['total'])
            non_ap_summary.append({
                'file': pdf_file,
                'line_items': len(records),
                'total_amount': total_amount
            })
            
            all_non_ap_results.extend(records)
            
        except Exception as e:
            print(f"  -> ERROR: {str(e)[:50]}...")
            non_ap_summary.append({
                'file': pdf_file,
                'line_items': 0,
                'total_amount': 0,
                'error': str(e)
            })
    
    # Display detailed results
    print(f"\n=== DETAILED RESULTS ===\n")
    
    print("AP INVOICES:")
    print("-" * 60)
    for summary in ap_summary[:5]:  # Show first 5
        print(f"{summary['file']}")
        print(f"  Line items: {summary['line_items']}")
        print(f"  Total: {summary['total_amount']:,.2f}" if summary['total_amount'] else "  Total: N/A")
        if 'error' in summary:
            print(f"  Error: {summary['error'][:50]}...")
        print()
    
    if len(ap_summary) > 5:
        print(f"... and {len(ap_summary) - 5} more AP invoices\n")
    
    print("\nNON-AP INVOICES:")
    print("-" * 60)
    for summary in non_ap_summary[:5]:  # Show first 5
        print(f"{summary['file']}")
        print(f"  Line items: {summary['line_items']}")
        print(f"  Total: {summary['total_amount']:,.2f}" if summary['total_amount'] else "  Total: N/A")
        if 'error' in summary:
            print(f"  Error: {summary['error'][:50]}...")
        print()
    
    if len(non_ap_summary) > 5:
        print(f"... and {len(non_ap_summary) - 5} more Non-AP invoices\n")
    
    # Save comprehensive results
    results = {
        "summary": {
            "total_files": len(pdf_files),
            "google_ap_files": len(google_ap_files),
            "google_non_ap_files": len(google_non_ap_files),
            "non_google_files": len(non_google_files),
            "total_ap_line_items": len(all_ap_results),
            "total_non_ap_line_items": len(all_non_ap_results),
            "ap_total_amount": sum(r['total'] for r in all_ap_results if r['total']),
            "non_ap_total_amount": sum(r['total'] for r in all_non_ap_results if r['total'])
        },
        "ap_files_summary": ap_summary,
        "non_ap_files_summary": non_ap_summary,
        "sample_ap_records": all_ap_results[:10],  # First 10 AP records
        "sample_non_ap_records": all_non_ap_results[:10]  # First 10 Non-AP records
    }
    
    with open('google_invoices_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Google AP invoices: {len(google_ap_files)} files, {len(all_ap_results)} line items")
    print(f"Google Non-AP invoices: {len(google_non_ap_files)} files, {len(all_non_ap_results)} line items")
    print(f"Total amount (AP): {results['summary']['ap_total_amount']:,.2f} THB")
    print(f"Total amount (Non-AP): {results['summary']['non_ap_total_amount']:,.2f} THB")
    print(f"\nFull results saved to: google_invoices_test_results.json")

if __name__ == "__main__":
    test_all_google_invoices()