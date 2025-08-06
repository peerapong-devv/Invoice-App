import sys
import os
import json
import fitz
sys.path.append('backend')

from backend.comprehensive_google_parser import parse_google_invoice_comprehensive, validate_comprehensive_totals, reconstruct_pk_patterns_comprehensive

def process_all_google_invoices():
    """Process all Google invoices and classify them"""
    
    invoice_folder = "Invoice for testing"
    results = []
    
    if not os.path.exists(invoice_folder):
        print(f"Folder {invoice_folder} not found")
        return
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(invoice_folder) if f.endswith('.pdf')]
    
    print(f"Processing {len(pdf_files)} PDF files...")
    print("=" * 80)
    
    ap_invoices = []
    non_ap_invoices = []
    non_google_invoices = []
    error_invoices = []
    
    for i, filename in enumerate(sorted(pdf_files), 1):
        filepath = os.path.join(invoice_folder, filename)
        
        try:
            # Extract text from PDF
            with fitz.open(filepath) as doc:
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
            
            # Parse the invoice
            records = parse_google_invoice_comprehensive(full_text, filename)
            validation = validate_comprehensive_totals(records)
            
            # Extract invoice details
            invoice_match = None
            import re
            invoice_match = re.search(r"(?:Invoice number|หมายเลขใบแจ้งหนี้):\s*([\w-]+)", full_text, re.IGNORECASE)
            invoice_id = invoice_match.group(1).strip() if invoice_match else filename.replace('.pdf', '')
            
            # Group records by type
            campaigns = [r for r in records if r.get('item_type') == 'Campaign']
            refunds = [r for r in records if r.get('item_type') == 'Refund']
            fees = [r for r in records if r.get('item_type') == 'Fee']
            
            invoice_data = {
                "filename": filename,
                "invoice_id": invoice_id,
                "invoice_type": "AP" if is_ap else "Non-AP",
                "invoice_total": validation['invoice_total'],
                "calculated_total": validation['calculated_total'],
                "difference": validation['difference'],
                "validation_passed": validation['valid'],      
                "total_records": len(records),
                "campaigns": len(campaigns),
                "refunds": len(refunds),
                "fees": len(fees),
                "campaign_total": sum(r['total'] for r in campaigns),
                "refund_total": sum(r['total'] for r in refunds),
                "fee_total": sum(r['total'] for r in fees)
            }
            
            if is_ap:
                ap_invoices.append(invoice_data)
            else:
                non_ap_invoices.append(invoice_data)
            
            results.append(invoice_data)
            
            # Print progress
            status = "✓" if validation['valid'] else "✗"
            print(f"{i:3}. {filename}")
            print(f"     Type: {invoice_data['invoice_type']}")
            print(f"     ID: {invoice_id}")
            if invoice_data['invoice_total']:
                print(f"     Total: ฿{invoice_data['invoice_total']:,.2f}")
            print(f"     Records: {len(records)} (C:{len(campaigns)}, R:{len(refunds)}, F:{len(fees)})")
            print(f"     Validation: {status}")
            
        except Exception as e:
            error_invoices.append({"filename": filename, "error": str(e)})
            print(f"{i:3}. {filename} - ERROR: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    
    print(f"Total files processed: {len(pdf_files)}")
    print(f"Google invoices: {len(results)}")
    print(f"Non-Google invoices: {len(non_google_invoices)}")
    print(f"Errors: {len(error_invoices)}")
    print()
    
    # AP Invoices Summary
    print(f"📊 AP INVOICES: {len(ap_invoices)}")
    if ap_invoices:
        ap_total = sum(inv['invoice_total'] for inv in ap_invoices if inv['invoice_total'])
        ap_passed = len([inv for inv in ap_invoices if inv['validation_passed']])
        print(f"   Total amount: ฿{ap_total:,.2f}")
        print(f"   Validation passed: {ap_passed}/{len(ap_invoices)}")
        
        print("   Top AP invoices by amount:")
        sorted_ap = sorted([inv for inv in ap_invoices if inv['invoice_total']], 
                          key=lambda x: x['invoice_total'], reverse=True)
        for inv in sorted_ap[:5]:
            print(f"     {inv['filename']}: ฿{inv['invoice_total']:,.2f}")
    
    print()
    
    # Non-AP Invoices Summary  
    print(f"📊 NON-AP INVOICES: {len(non_ap_invoices)}")
    if non_ap_invoices:
        nonap_total = sum(inv['invoice_total'] for inv in non_ap_invoices if inv['invoice_total'])
        nonap_passed = len([inv for inv in non_ap_invoices if inv['validation_passed']])
        print(f"   Total amount: ฿{nonap_total:,.2f}")
        print(f"   Validation passed: {nonap_passed}/{len(non_ap_invoices)}")
        
        print("   Top Non-AP invoices by amount:")
        sorted_nonap = sorted([inv for inv in non_ap_invoices if inv['invoice_total']], 
                             key=lambda x: x['invoice_total'], reverse=True)
        for inv in sorted_nonap[:5]:
            print(f"     {inv['filename']}: ฿{inv['invoice_total']:,.2f}")
    
    # Refunds Summary
    invoices_with_refunds = [inv for inv in results if inv['refunds'] > 0]
    if invoices_with_refunds:
        print(f"\n📊 INVOICES WITH REFUNDS: {len(invoices_with_refunds)}")
        total_refunds = sum(inv['refund_total'] for inv in invoices_with_refunds)
        print(f"   Total refund amount: ฿{total_refunds:,.2f}")
        
        for inv in invoices_with_refunds:
            print(f"     {inv['filename']}: {inv['refunds']} refunds = ฿{inv['refund_total']:,.2f}")
    
    # Save detailed results
    output_data = {
        "summary": {
            "total_files": len(pdf_files),
            "google_invoices": len(results),
            "ap_invoices": len(ap_invoices),
            "non_ap_invoices": len(non_ap_invoices),
            "non_google_invoices": len(non_google_invoices),
            "errors": len(error_invoices)
        },
        "ap_invoices": ap_invoices,
        "non_ap_invoices": non_ap_invoices,
        "invoices_with_refunds": invoices_with_refunds,
        "errors": error_invoices
    }
    
    with open('google_invoices_classification.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Detailed results saved to: google_invoices_classification.json")
    
    return results

if __name__ == "__main__":
    process_all_google_invoices()