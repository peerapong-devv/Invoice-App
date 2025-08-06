import sys
import os
import json
import fitz
sys.path.append('backend')

from backend.perfect_google_parser import parse_google_invoice_perfect, validate_perfect_totals, detect_ap_perfect, reconstruct_pk_patterns_perfect

def final_perfect_test():
    """Final test of perfect parser with all Google invoices"""
    
    invoice_folder = "Invoice for testing"
    pdf_files = [f for f in os.listdir(invoice_folder) if (f.startswith('529') or f.startswith('530')) and f.endswith('.pdf')]
    
    print(f"FINAL PERFECT TEST: {len(pdf_files)} Google invoices")
    print("=" * 100)
    
    results = []
    ap_count = 0
    non_ap_count = 0
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
            
            # Parse with perfect parser
            records = parse_google_invoice_perfect(full_text, filename)
            validation = validate_perfect_totals(records)
            
            # Check AP/Non-AP with perfect detection (clean text first)
            clean_text = full_text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
            reconstructed = reconstruct_pk_patterns_perfect(clean_text)
            is_ap = detect_ap_perfect(reconstructed)
            
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
                "fees": len(fees),
                "refund_amounts": [r['total'] for r in refunds] if refunds else []
            }
            
            results.append(invoice_data)
            
            if is_ap:
                ap_count += 1
            else:
                non_ap_count += 1
            
            total_invoices += 1
            if validation['valid']:
                validation_passed += 1
            
            # Print results
            status = "PASS" if validation['valid'] else "FAIL"
            total_str = f"{validation['invoice_total']:,.2f}" if validation['invoice_total'] else "N/A"
            calc_str = f"{validation['calculated_total']:,.2f}"
            
            print(f"{i:2}. {filename}")
            print(f"    Type: {invoice_data['invoice_type']} | ID: {invoice_id}")
            print(f"    Total: {total_str} vs Calc: {calc_str} THB")
            print(f"    Records: {len(records)} (C:{len(campaigns)}, R:{len(refunds)}, F:{len(fees)}) | {status}")
            
            # Show refund details if any
            if refunds:
                refund_ranges = {
                    'small': [r for r in refunds if -100 <= r['total'] < 0],
                    'medium': [r for r in refunds if -1000 <= r['total'] < -100], 
                    'large': [r for r in refunds if -10000 <= r['total'] < -1000],
                    'huge': [r for r in refunds if r['total'] < -10000]
                }
                
                range_summary = []
                for range_name, range_refunds in refund_ranges.items():
                    if range_refunds:
                        amounts = [r['total'] for r in range_refunds]
                        range_summary.append(f"{range_name.upper()}({len(amounts)}): {amounts}")
                
                print(f"    Refunds: {' | '.join(range_summary)}")
            
        except Exception as e:
            print(f"{i:2}. {filename} - ERROR: {str(e)}")
            results.append({
                "filename": filename,
                "error": str(e)
            })
    
    # Final Summary
    print("\n" + "=" * 100)
    print("FINAL PERFECT TEST SUMMARY")
    print("=" * 100)
    
    successful_results = [r for r in results if 'error' not in r]
    error_results = [r for r in results if 'error' in r]
    
    print(f"Total Google invoices: {total_invoices}")
    print(f"AP invoices: {ap_count}")
    print(f"Non-AP invoices: {non_ap_count}")
    print(f"Validation passed: {validation_passed}/{total_invoices} ({validation_passed/total_invoices*100:.1f}%)")
    print(f"Processing errors: {len(error_results)}")
    
    if successful_results:
        # AP vs Non-AP breakdown
        ap_invoices = [r for r in successful_results if r['invoice_type'] == 'AP']
        non_ap_invoices = [r for r in successful_results if r['invoice_type'] == 'Non-AP']
        
        if ap_invoices:
            ap_total = sum(inv['invoice_total'] for inv in ap_invoices if inv['invoice_total'])
            ap_passed = len([inv for inv in ap_invoices if inv['validation_passed']])
            print(f"\nAP INVOICES SUMMARY:")
            print(f"  Count: {len(ap_invoices)}")
            print(f"  Total amount: {ap_total:,.2f} THB")
            print(f"  Validation passed: {ap_passed}/{len(ap_invoices)}")
        
        if non_ap_invoices:
            nonap_total = sum(inv['invoice_total'] for inv in non_ap_invoices if inv['invoice_total'])
            nonap_passed = len([inv for inv in non_ap_invoices if inv['validation_passed']])
            print(f"\nNON-AP INVOICES SUMMARY:")
            print(f"  Count: {len(non_ap_invoices)}")
            print(f"  Total amount: {nonap_total:,.2f} THB")
            print(f"  Validation passed: {nonap_passed}/{len(non_ap_invoices)}")
        
        # Refund analysis
        all_refunds = []
        for r in successful_results:
            all_refunds.extend(r['refund_amounts'])
        
        if all_refunds:
            refund_ranges = {
                'small': [r for r in all_refunds if -100 <= r < 0],
                'medium': [r for r in all_refunds if -1000 <= r < -100],
                'large': [r for r in all_refunds if -10000 <= r < -1000], 
                'huge': [r for r in all_refunds if r < -10000]
            }
            
            print(f"\nREFUND ANALYSIS:")
            print(f"  Total refunds found: {len(all_refunds)}")
            for range_name, range_amounts in refund_ranges.items():
                if range_amounts:
                    total_amount = sum(range_amounts)
                    print(f"  {range_name.upper()} refunds: {len(range_amounts)} (total: {total_amount:,.2f} THB)")
    
    # Save results
    final_results = {
        "summary": {
            "total_invoices": total_invoices,
            "ap_invoices": ap_count,
            "non_ap_invoices": non_ap_count,
            "validation_passed": validation_passed,
            "validation_rate": validation_passed/total_invoices if total_invoices > 0 else 0,
            "processing_errors": len(error_results)
        },
        "invoices": successful_results,
        "errors": error_results
    }
    
    with open('final_perfect_results.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nFinal results saved to: final_perfect_results.json")
    
    # Return success metrics
    success_rate = validation_passed / total_invoices if total_invoices > 0 else 0
    ap_detection_rate = ap_count / total_invoices if total_invoices > 0 else 0
    
    return {
        "success_rate": success_rate,
        "ap_detection_rate": ap_detection_rate,
        "validation_passed": validation_passed,
        "total_invoices": total_invoices
    }

if __name__ == "__main__":
    final_perfect_test()