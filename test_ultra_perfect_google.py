import sys
import os
import json
import fitz
sys.path.append('backend')

from backend.ultra_perfect_google_parser import parse_google_invoice_ultra, validate_ultra_totals, detect_ap_ultra, clean_and_fix_text

def test_ultra_perfect_google():
    """Test ultra perfect parser with all Google invoices"""
    
    invoice_folder = "Invoice for testing"
    pdf_files = [f for f in os.listdir(invoice_folder) if (f.startswith('529') or f.startswith('530')) and f.endswith('.pdf')]
    
    print(f"ULTRA PERFECT TEST: {len(pdf_files)} Google invoices")
    print("=" * 100)
    
    results = []
    ap_count = 0
    non_ap_count = 0
    validation_passed = 0
    total_invoices = 0
    
    # Track improvements vs original results
    improvements = {
        'null_total_fixed': 0,
        'large_diff_fixed': 0,
        'credit_note_fixed': 0,
        'validation_improved': 0
    }
    
    # Known problem cases from analysis
    problem_cases = {
        '5297692790.pdf': {'issue': 'null_total', 'expected_total': -6284.42},
        '5298528895.pdf': {'issue': 'null_total', 'expected_total': 35397.74},
        '5298281913.pdf': {'issue': 'null_total', 'expected_total': -2.87},
        '5302951835.pdf': {'issue': 'credit_note', 'expected_total': -2543.65},
        '5297830454.pdf': {'issue': 'large_diff', 'expected_type': 'AP'},
        '5298134610.pdf': {'issue': 'large_diff', 'expected_type': 'AP'},
        '5298157309.pdf': {'issue': 'large_diff', 'expected_type': 'AP'},
        '5298361576.pdf': {'issue': 'large_diff', 'expected_type': 'AP'},
    }
    
    for i, filename in enumerate(sorted(pdf_files), 1):
        filepath = os.path.join(invoice_folder, filename)
        
        try:
            # Extract text
            with fitz.open(filepath) as doc:
                full_text = ""
                for page in doc:
                    full_text += page.get_text() + "\n"
            
            # Parse with ultra perfect parser
            records = parse_google_invoice_ultra(full_text, filename)
            validation = validate_ultra_totals(records)
            
            # Check AP/Non-AP with ultra detection
            clean_text = clean_and_fix_text(full_text)
            is_ap = detect_ap_ultra(clean_text)
            
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
            
            # Check for improvements in problem cases
            if filename in problem_cases:
                problem = problem_cases[filename]
                
                if problem['issue'] == 'null_total':
                    if validation['invoice_total'] is not None:
                        improvements['null_total_fixed'] += 1
                        print(f"    FIXED NULL TOTAL: {filename} now has total: {validation['invoice_total']:,.2f}")
                
                elif problem['issue'] == 'credit_note':
                    if validation['invoice_total'] is not None and validation['valid']:
                        improvements['credit_note_fixed'] += 1
                        print(f"    FIXED CREDIT NOTE: {filename} validation now passes")
                
                elif problem['issue'] == 'large_diff':
                    if validation['valid']:
                        improvements['large_diff_fixed'] += 1
                        print(f"    FIXED LARGE DIFF: {filename} validation now passes")
            
            if is_ap:
                ap_count += 1
            else:
                non_ap_count += 1
            
            total_invoices += 1
            if validation['valid']:
                validation_passed += 1
            
            # Print results
            status = "PASS" if validation['valid'] else "FAIL"
            total_str = f"{validation['invoice_total']:,.2f}" if validation['invoice_total'] is not None else "NULL"
            calc_str = f"{validation['calculated_total']:,.2f}"
            
            # Special formatting for problem cases
            prefix = "**" if filename in problem_cases else "  "
            
            print(f"{prefix}{i:2}. {filename}")
            print(f"     Type: {invoice_data['invoice_type']} | ID: {invoice_id}")
            print(f"     Total: {total_str} vs Calc: {calc_str} THB")
            print(f"     Records: {len(records)} (C:{len(campaigns)}, R:{len(refunds)}, F:{len(fees)}) | {status}")
            
            if not validation['valid'] and validation['invoice_total'] is not None:
                print(f"     Diff: {validation['difference']:,.2f} THB (tolerance: {validation.get('tolerance', 0):,.2f})")
            
        except Exception as e:
            print(f"{i:2}. {filename} - ERROR: {str(e)}")
            results.append({
                "filename": filename,
                "error": str(e)
            })
    
    # Final Summary
    print("\n" + "=" * 100)
    print("ULTRA PERFECT TEST SUMMARY")
    print("=" * 100)
    
    successful_results = [r for r in results if 'error' not in r]
    error_results = [r for r in results if 'error' in r]
    
    print(f"Total Google invoices: {total_invoices}")
    print(f"AP invoices: {ap_count}")
    print(f"Non-AP invoices: {non_ap_count}")
    print(f"Validation passed: {validation_passed}/{total_invoices} ({validation_passed/total_invoices*100:.1f}%)")
    print(f"Processing errors: {len(error_results)}")
    
    # Improvements summary
    print(f"\nIMPROVEMENTS FROM ULTRA PARSER:")
    print(f"   Null totals fixed: {improvements['null_total_fixed']}")
    print(f"   Large differences fixed: {improvements['large_diff_fixed']}")
    print(f"   Credit notes fixed: {improvements['credit_note_fixed']}")
    
    # Detailed breakdown
    if successful_results:
        # Validation rate comparison
        validation_rate = validation_passed / total_invoices * 100
        print(f"\nVALIDATION RATE: {validation_rate:.1f}% (vs original ~70%)")
        
        # Problem cases that still need work
        still_failing = []
        for result in successful_results:
            if result['filename'] in problem_cases and not result['validation_passed']:
                still_failing.append(result['filename'])
        
        if still_failing:
            print(f"\nSTILL FAILING PROBLEM CASES:")
            for filename in still_failing:
                result = next(r for r in successful_results if r['filename'] == filename)
                print(f"   {filename}: {result.get('difference', 0):,.2f} THB difference")
        
        # Files with null totals
        null_totals = [r for r in successful_results if r['invoice_total'] is None]
        if null_totals:
            print(f"\nSTILL NULL TOTALS ({len(null_totals)} files):")
            for result in null_totals[:10]:  # Show first 10
                print(f"   {result['filename']}: {result['invoice_type']}, calc: {result['calculated_total']:,.2f}")
    
    # Save results
    ultra_results = {
        "summary": {
            "total_invoices": total_invoices,
            "ap_invoices": ap_count,
            "non_ap_invoices": non_ap_count,
            "validation_passed": validation_passed,
            "validation_rate": validation_passed/total_invoices if total_invoices > 0 else 0,
            "processing_errors": len(error_results),
            "improvements": improvements
        },
        "invoices": successful_results,
        "errors": error_results
    }
    
    with open('ultra_perfect_results.json', 'w', encoding='utf-8') as f:
        json.dump(ultra_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nUltra results saved to: ultra_perfect_results.json")
    
    return ultra_results

if __name__ == "__main__":
    results = test_ultra_perfect_google()