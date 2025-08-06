import sys
import os
import json
import fitz
sys.path.append('backend')

from backend.learned_google_parser import parse_google_invoice_learned, validate_learned_totals, reconstruct_pk_patterns_learned

def test_learned_parser():
    """Test the learned parser with all Google invoices"""
    
    invoice_folder = "Invoice for testing"
    
    # Get all PDF files starting with 529 (Google invoices)
    pdf_files = [f for f in os.listdir(invoice_folder) if f.startswith('529') and f.endswith('.pdf')]
    
    print(f"Testing learned parser with {len(pdf_files)} Google invoices...")
    print("=" * 80)
    
    ap_invoices = []
    non_ap_invoices = []
    validation_passed = 0
    total_invoices = 0
    
    for i, filename in enumerate(sorted(pdf_files), 1):
        filepath = os.path.join(invoice_folder, filename)
        
        try:
            # Extract text
            with fitz.open(filepath) as doc:
                full_text = ""
                for page in doc:
                    full_text += page.get_text() + "\n"
            
            # Parse with learned parser
            records = parse_google_invoice_learned(full_text, filename)
            validation = validate_learned_totals(records)
            
            # Check AP/Non-AP after reconstruction
            reconstructed = reconstruct_pk_patterns_learned(full_text)
            is_ap = bool('pk|' in reconstructed)
            
            # Extract invoice ID
            import re
            invoice_match = re.search(r"(?:Invoice number|หมายเลขใบแจ้งหนี้):\s*([\w-]+)", full_text, re.IGNORECASE)
            invoice_id = invoice_match.group(1).strip() if invoice_match else filename.replace('.pdf', '')
            
            # Group records
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
                "fees": len(fees)
            }
            
            if is_ap:
                ap_invoices.append(invoice_data)
            else:
                non_ap_invoices.append(invoice_data)
            
            total_invoices += 1
            if validation['valid']:
                validation_passed += 1
            
            # Print progress
            status = "PASS" if validation['valid'] else "FAIL"
            total_str = f"{validation['invoice_total']:,.2f}" if validation['invoice_total'] else "N/A"
            calc_str = f"{validation['calculated_total']:,.2f}"
            
            print(f"{i:2}. {filename}")
            print(f"    Type: {invoice_data['invoice_type']} | ID: {invoice_id}")
            print(f"    Total: {total_str} vs Calc: {calc_str} THB")
            print(f"    Records: {len(records)} (C:{len(campaigns)}, R:{len(refunds)}, F:{len(fees)}) | {status}")
            
            if refunds:
                refund_amounts = [r['total'] for r in refunds]
                print(f"    Refunds: {refund_amounts}")
            
        except Exception as e:
            print(f"{i:2}. {filename} - ERROR: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("LEARNED PARSER TEST SUMMARY")
    print("=" * 80)
    
    print(f"Total Google invoices: {total_invoices}")
    print(f"AP invoices: {len(ap_invoices)}")
    print(f"Non-AP invoices: {len(non_ap_invoices)}")
    print(f"Validation passed: {validation_passed}/{total_invoices} ({validation_passed/total_invoices*100:.1f}%)")
    
    if ap_invoices:
        ap_total = sum(inv['invoice_total'] for inv in ap_invoices if inv['invoice_total'])
        ap_passed = len([inv for inv in ap_invoices if inv['validation_passed']])
        print(f"\nAP Summary:")
        print(f"  Total amount: {ap_total:,.2f} THB")
        print(f"  Validation passed: {ap_passed}/{len(ap_invoices)}")
    
    if non_ap_invoices:
        nonap_total = sum(inv['invoice_total'] for inv in non_ap_invoices if inv['invoice_total'])
        nonap_passed = len([inv for inv in non_ap_invoices if inv['validation_passed']])
        print(f"\nNon-AP Summary:")
        print(f"  Total amount: {nonap_total:,.2f} THB")
        print(f"  Validation passed: {nonap_passed}/{len(non_ap_invoices)}")
    
    # Invoices with refunds
    invoices_with_refunds = [inv for inv in ap_invoices + non_ap_invoices if inv['refunds'] > 0]
    if invoices_with_refunds:
        print(f"\nInvoices with refunds: {len(invoices_with_refunds)}")
        for inv in invoices_with_refunds:
            print(f"  {inv['filename']}: {inv['refunds']} refunds")
    
    # Save results
    results = {
        "summary": {
            "total_invoices": total_invoices,
            "ap_invoices": len(ap_invoices),
            "non_ap_invoices": len(non_ap_invoices),
            "validation_passed": validation_passed,
            "validation_rate": validation_passed/total_invoices if total_invoices > 0 else 0
        },
        "ap_invoices": ap_invoices,
        "non_ap_invoices": non_ap_invoices,
        "invoices_with_refunds": invoices_with_refunds
    }
    
    with open('learned_parser_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: learned_parser_results.json")
    
    return results

if __name__ == "__main__":
    test_learned_parser()