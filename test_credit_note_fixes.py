#!/usr/bin/env python3
"""
Test script to verify credit note fixes in the Google parser
"""

import fitz
import sys
import os

# Add backend to path
sys.path.append('backend')

from perfect_google_parser import parse_google_invoice_perfect, validate_perfect_totals

def test_credit_note_files():
    """Test all problematic credit note files"""
    
    # Credit note files with issues from the original request
    credit_files = [
        '5297692790.pdf',  # showing 0 calculated, but should find credit amounts
        '5297785878.pdf',  # finds -1.66 but no invoice total  
        '5298281913.pdf',  # finds -2.87 but no invoice total
        '5298615229.pdf',  # showing 0 calculated
        '5300482566.pdf',  # showing 0 calculated
        '5301461407.pdf',  # showing 0 calculated
        '5302012325.pdf',  # showing 0 calculated
        '5302293067.pdf',  # showing 0 calculated
        '5302788327.pdf',  # showing 0 calculated
        '5303158396.pdf',  # finds -0.83 but no invoice total
        '5303649115.pdf',  # finds -0.39 but no invoice total
    ]
    
    results = []
    
    for filename in credit_files:
        filepath = f"Invoice for testing\\{filename}"
        
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filename}")
            continue
            
        try:
            # Extract text from PDF
            with fitz.open(filepath) as doc:
                full_text = ""
                for page in doc:
                    full_text += page.get_text() + "\n"
            
            # Parse with enhanced parser
            records = parse_google_invoice_perfect(full_text, filename)
            validation = validate_perfect_totals(records)
            
            # Analyze results
            refunds = [r for r in records if r.get('item_type') == 'Refund']
            campaigns = [r for r in records if r.get('item_type') == 'Campaign'] 
            fees = [r for r in records if r.get('item_type') == 'Fee']
            
            result = {
                'filename': filename,
                'total_records': len(records),
                'campaigns': len(campaigns),
                'refunds': len(refunds), 
                'fees': len(fees),
                'invoice_total': validation.get('invoice_total'),
                'calculated_total': validation.get('calculated_total'),
                'validation_passed': validation.get('valid', False),
                'validation_message': validation.get('message', ''),
                'is_credit_note': (validation.get('invoice_total') or 0) < 0,
                'records': records[:3]  # Show first 3 records for inspection
            }
            
            results.append(result)
            
        except Exception as e:
            print(f"ERROR processing {filename}: {e}")
            results.append({
                'filename': filename,
                'error': str(e)
            })
    
    return results

def print_results(results):
    """Print test results in a readable format"""
    
    print("=" * 80)
    print("CREDIT NOTE PARSER TEST RESULTS")
    print("=" * 80)
    
    success_count = 0
    total_count = 0
    
    for result in results:
        filename = result['filename']
        print(f"\n{filename}")
        print("-" * 60)
        
        if 'error' in result:
            print(f"ERROR: {result['error']}")
            continue
            
        total_count += 1
        
        invoice_total = result['invoice_total']
        calc_total = result['calculated_total']
        is_credit = result['is_credit_note']
        
        print(f"Credit Note: {'YES' if is_credit else 'NO'}")
        
        if invoice_total is not None:
            print(f"Invoice Total: {invoice_total:,.2f} THB")
        else:
            print(f"Invoice Total: NOT FOUND")
            
        print(f"Calculated Total: {calc_total:,.2f} THB")
        
        validation_passed = result['validation_passed']
        if validation_passed:
            print(f"Validation: PASSED - {result['validation_message']}")
            if invoice_total is not None:
                success_count += 1
        else:
            print(f"Validation: FAILED - {result['validation_message']}")
        
        print(f"Records: {result['total_records']} total (C:{result['campaigns']}, R:{result['refunds']}, F:{result['fees']})")
        
        # Show sample records
        if result['records']:
            print("Sample Records:")
            for i, record in enumerate(result['records'], 1):
                item_type = record.get('item_type', 'Unknown')
                total = record.get('total', 0)
                desc = record.get('description', '')[:50]
                try:
                    print(f"   {i}. {item_type}: {total:,.2f} - {desc}...")
                except UnicodeEncodeError:
                    print(f"   {i}. {item_type}: {total:,.2f} - [description contains Thai text]")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Success Rate: {success_count}/{total_count} files")
    if total_count > 0:
        print(f"Success Percentage: {(success_count/total_count)*100:.1f}%")
    
    # Show files that still need work
    failed_files = [r['filename'] for r in results if 'error' not in r and not r['validation_passed']]
    if failed_files:
        print(f"\nFiles still needing fixes:")
        for filename in failed_files:
            print(f"   - {filename}")

if __name__ == "__main__":
    print("Testing credit note parser fixes...")
    results = test_credit_note_files()
    print_results(results)