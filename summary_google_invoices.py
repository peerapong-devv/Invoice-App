import sys
import os
import json
import fitz
sys.path.append('backend')

from backend.comprehensive_google_parser import parse_google_invoice_comprehensive, validate_comprehensive_totals, reconstruct_pk_patterns_comprehensive

def summarize_google_invoices():
    """Summarize all Google invoices classification"""
    
    invoice_folder = "Invoice for testing"
    
    if not os.path.exists(invoice_folder):
        print(f"Folder {invoice_folder} not found")
        return
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(invoice_folder) if f.endswith('.pdf')]
    
    ap_invoices = []
    non_ap_invoices = []
    non_google_invoices = []
    error_invoices = []
    
    print("Processing Google invoices...")
    print("=" * 60)
    
    for filename in sorted(pdf_files):
        try:
            # Extract text from PDF
            with fitz.open(os.path.join(invoice_folder, filename)) as doc:
                full_text = ""
                for page in doc:
                    full_text += page.get_text() + "\n"
            
            # Check if it's a Google invoice
            is_google = "google" in full_text.lower() and "ads" in full_text.lower()
            
            if not is_google:
                non_google_invoices.append(filename)
                continue
            
            # Reconstruct pk patterns and check AP/Non-AP
            reconstructed = reconstruct_pk_patterns_comprehensive(full_text)
            is_ap = bool('pk|' in reconstructed)
            
            # Parse the invoice for basic details
            records = parse_google_invoice_comprehensive(full_text, filename)
            validation = validate_comprehensive_totals(records)
            
            # Extract invoice ID
            import re
            invoice_match = re.search(r"(?:Invoice number|หมายเลขใบแจ้งหนี้):\s*([\w-]+)", full_text, re.IGNORECASE)
            invoice_id = invoice_match.group(1).strip() if invoice_match else filename.replace('.pdf', '')
            
            invoice_data = {
                "filename": filename,
                "invoice_id": invoice_id,
                "invoice_type": "AP" if is_ap else "Non-AP",
                "invoice_total": validation['invoice_total'],
                "validation_passed": validation['valid'],
                "total_records": len(records)
            }
            
            if is_ap:
                ap_invoices.append(invoice_data)
            else:
                non_ap_invoices.append(invoice_data)
                
        except Exception as e:
            error_invoices.append({"filename": filename, "error": str(e)})
    
    # Print summary
    print("GOOGLE INVOICES CLASSIFICATION SUMMARY")
    print("=" * 60)
    
    print(f"Total PDF files: {len(pdf_files)}")
    print(f"Google invoices: {len(ap_invoices) + len(non_ap_invoices)}")
    print(f"Non-Google invoices: {len(non_google_invoices)}")
    print(f"Processing errors: {len(error_invoices)}")
    print()
    
    # AP Invoices
    print(f"AP INVOICES: {len(ap_invoices)}")
    if ap_invoices:
        ap_total = sum(inv['invoice_total'] for inv in ap_invoices if inv['invoice_total'])
        ap_passed = len([inv for inv in ap_invoices if inv['validation_passed']])
        print(f"  Total amount: {ap_total:,.2f} THB")
        print(f"  Validation passed: {ap_passed}/{len(ap_invoices)}")
        
        print("  AP Invoices list:")
        for inv in sorted(ap_invoices, key=lambda x: x['invoice_total'] or 0, reverse=True):
            total_str = f"{inv['invoice_total']:,.2f}" if inv['invoice_total'] else "N/A"
            status = "PASS" if inv['validation_passed'] else "FAIL"
            print(f"    {inv['filename']} (ID: {inv['invoice_id']}): {total_str} THB - {status}")
    
    print()
    
    # Non-AP Invoices
    print(f"NON-AP INVOICES: {len(non_ap_invoices)}")
    if non_ap_invoices:
        nonap_total = sum(inv['invoice_total'] for inv in non_ap_invoices if inv['invoice_total'])
        nonap_passed = len([inv for inv in non_ap_invoices if inv['validation_passed']])
        print(f"  Total amount: {nonap_total:,.2f} THB")
        print(f"  Validation passed: {nonap_passed}/{len(non_ap_invoices)}")
        
        print("  Non-AP Invoices list:")
        for inv in sorted(non_ap_invoices, key=lambda x: x['invoice_total'] or 0, reverse=True):
            total_str = f"{inv['invoice_total']:,.2f}" if inv['invoice_total'] else "N/A"
            status = "PASS" if inv['validation_passed'] else "FAIL"
            print(f"    {inv['filename']} (ID: {inv['invoice_id']}): {total_str} THB - {status}")
    
    # Save summary data
    summary_data = {
        "summary": {
            "total_files": len(pdf_files),
            "google_invoices": len(ap_invoices) + len(non_ap_invoices),
            "ap_invoices": len(ap_invoices),
            "non_ap_invoices": len(non_ap_invoices),
            "non_google_invoices": len(non_google_invoices),
            "errors": len(error_invoices),
            "ap_total_amount": sum(inv['invoice_total'] for inv in ap_invoices if inv['invoice_total']),
            "nonap_total_amount": sum(inv['invoice_total'] for inv in non_ap_invoices if inv['invoice_total'])
        },
        "ap_invoices": ap_invoices,
        "non_ap_invoices": non_ap_invoices,
        "errors": error_invoices
    }
    
    with open('google_invoices_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    print()
    print("Detailed results saved to: google_invoices_summary.json")
    
    return summary_data

if __name__ == "__main__":
    summarize_google_invoices()