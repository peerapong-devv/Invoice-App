import sys
import os
import json
import fitz
sys.path.append('backend')

from backend.comprehensive_google_parser import parse_google_invoice_comprehensive, validate_comprehensive_totals

def test_all_google_invoices():
    """Test the precise parser with all Google invoices"""
    
    invoice_folder = "Invoice for testing"
    results = []
    
    if not os.path.exists(invoice_folder):
        print(f"Folder {invoice_folder} not found")
        return
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(invoice_folder) if f.endswith('.pdf')]
    
    print(f"Found {len(pdf_files)} PDF files to test")
    print("=" * 60)
    
    ap_count = 0
    non_ap_count = 0
    error_count = 0
    
    for i, filename in enumerate(sorted(pdf_files), 1):
        filepath = os.path.join(invoice_folder, filename)
        
        try:
            print(f"\n{i:2}. Processing {filename}...")
            
            # Extract text from PDF
            with fitz.open(filepath) as doc:
                full_text = ""
                for page in doc:
                    full_text += page.get_text() + "\n"
            
            # Check if it's a Google invoice
            if not ("google" in full_text.lower() and "ads" in full_text.lower()):
                print(f"    SKIP: Not a Google invoice")
                continue
            
            # Parse the invoice
            records = parse_google_invoice_comprehensive(full_text, filename)
            validation = validate_comprehensive_totals(records)
            
            # Determine invoice type
            is_ap = any('pk < /dev/null | ' in line for line in full_text.split('\n'))
            invoice_type = "AP" if is_ap else "Non-AP"
            
            if is_ap:
                ap_count += 1
            else:
                non_ap_count += 1
            
            # Group records by type
            campaigns = [r for r in records if r.get('item_type') == 'Campaign']
            refunds = [r for r in records if r.get('item_type') == 'Refund']
            fees = [r for r in records if r.get('item_type') == 'Fee']
            
            campaign_total = sum(r['total'] for r in campaigns)
            refund_total = sum(r['total'] for r in refunds)
            fee_total = sum(r['total'] for r in fees)
            calculated_total = campaign_total + refund_total + fee_total
            
            result = {
                "filename": filename,
                "invoice_type": invoice_type,
                "invoice_id": records[0].get('invoice_id') if records else None,
                "invoice_total": validation['invoice_total'],
                "calculated_total": calculated_total,
                "difference": validation['difference'],
                "validation_passed": validation['valid'],
                "total_records": len(records),
                "campaigns": len(campaigns),
                "refunds": len(refunds),
                "fees": len(fees),
                "campaign_total": campaign_total,
                "refund_total": refund_total,
                "fee_total": fee_total,
                "refund_amounts": [r['total'] for r in refunds] if refunds else []
            }
            
            results.append(result)
            
            # Print summary
            print(f"    Type: {invoice_type}")
            print(f"    Records: {len(records)} (C:{len(campaigns)}, R:{len(refunds)}, F:{len(fees)})")
            if validation['invoice_total']:
                print(f"    Total: {validation['invoice_total']:,.2f} THB vs Calculated: {calculated_total:,.2f} THB")
                if validation['valid']:
                    print(f"    Validation: PASSED")
                else:
                    print(f"    Validation: FAILED (Diff: {validation['difference']:,.2f} THB)")
            
            if refunds:
                print(f"    Refunds: {[f'{r:.2f}' for r in result['refund_amounts']]}")
            
        except Exception as e:
            error_count += 1
            print(f"    ERROR: {str(e)}")
            result = {
                "filename": filename,
                "error": str(e)
            }
            results.append(result)
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    
    successful_results = [r for r in results if 'error' not in r]
    error_results = [r for r in results if 'error' in r]
    
    print(f"Total files processed: {len(results)}")
    print(f"Successful: {len(successful_results)}")
    print(f"Errors: {len(error_results)}")
    print(f"AP invoices: {ap_count}")
    print(f"Non-AP invoices: {non_ap_count}")
    
    if successful_results:
        passed_validation = [r for r in successful_results if r.get('validation_passed', False)]
        print(f"Validation passed: {len(passed_validation)}/{len(successful_results)}")
        
        # Total records by type
        total_campaigns = sum(r.get('campaigns', 0) for r in successful_results)
        total_refunds = sum(r.get('refunds', 0) for r in successful_results)
        total_fees = sum(r.get('fees', 0) for r in successful_results)
        
        print(f"Total records: Campaigns={total_campaigns}, Refunds={total_refunds}, Fees={total_fees}")
        
        # Show invoices with refunds
        invoices_with_refunds = [r for r in successful_results if r.get('refunds', 0) > 0]
        if invoices_with_refunds:
            print(f"\nInvoices with refunds ({len(invoices_with_refunds)}):")
            for r in invoices_with_refunds:
                print(f"  {r['filename']}: {r['refunds']} refunds = {r['refund_amounts']}")
    
    # Save detailed results
    with open('google_invoice_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: google_invoice_test_results.json")
    
    return results

if __name__ == "__main__":
    test_all_google_invoices()
