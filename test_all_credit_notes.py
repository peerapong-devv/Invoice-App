import fitz
import sys
import os
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append('backend')

from enhanced_credit_note_parser import parse_google_credit_note_enhanced, validate_credit_note_totals

def test_all_credit_notes():
    """Test enhanced parser with all 12 credit note files"""
    
    credit_notes = [
        "5297692790.pdf",   # -6,284.42
        "5297785878.pdf",   # -1.66  
        "5298281913.pdf",   # -2.87
        "5298615229.pdf",   # -442.78
        "5300482566.pdf",   # -361.13
        "5301461407.pdf",
        "5302012325.pdf", 
        "5302293067.pdf",
        "5302788327.pdf",
        "5302951835.pdf",
        "5303158396.pdf",
        "5303649115.pdf"
    ]
    
    print("="*100)
    print("COMPREHENSIVE TEST OF ALL 12 CREDIT NOTE FILES")
    print("="*100)
    
    results = []
    
    for i, filename in enumerate(credit_notes):
        print(f"\n{i+1:2d}. Testing {filename}...")
        
        try:
            filepath = os.path.join("Invoice for testing", filename)
            
            # Extract text
            with fitz.open(filepath) as doc:
                text_content = "\n".join(page.get_text() for page in doc)
            
            # Parse using enhanced parser
            records = parse_google_credit_note_enhanced(text_content, filename)
            
            # Validate
            validation = validate_credit_note_totals(records)
            
            # Store results
            results.append({
                'filename': filename,
                'records': len(records),
                'valid': validation.get('is_valid', False),
                'invoice_total': validation.get('invoice_total', 0),
                'individual_sum': validation.get('individual_sum', 0),
                'difference': validation.get('difference', 0),
                'error': None
            })
            
            # Quick summary
            status = "✓ PASS" if validation.get('is_valid') else "✗ FAIL"
            print(f"    {status} - {len(records)} records, Total: {validation.get('invoice_total', 0):.2f}")
            
        except Exception as e:
            print(f"    ✗ ERROR - {str(e)}")
            results.append({
                'filename': filename,
                'records': 0,
                'valid': False,
                'invoice_total': 0,
                'individual_sum': 0,
                'difference': 0,
                'error': str(e)
            })
    
    # Summary table
    print("\n\n" + "="*100)
    print("FINAL SUMMARY OF ALL CREDIT NOTES")
    print("="*100)
    print(f"{'#':<3} {'Filename':<20} {'Records':<8} {'Valid':<6} {'Invoice Total':<13} {'Sum':<13} {'Diff':<8} {'Status'}")
    print("-" * 100)
    
    passed = 0
    failed = 0
    
    for i, result in enumerate(results):
        num = f"{i+1}."
        filename = result['filename']
        records = result['records']
        valid = "Yes" if result['valid'] else "No"
        total = result['invoice_total']
        sum_amt = result['individual_sum']
        diff = result['difference']
        
        if result['error']:
            status = f"ERROR: {result['error'][:20]}..."
            failed += 1
        elif result['valid']:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"{num:<3} {filename:<20} {records:<8} {valid:<6} {total:<13.2f} {sum_amt:<13.2f} {diff:<8.2f} {status}")
    
    print("-" * 100)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {len(credit_notes)} files")
    
    # Show problematic files
    if failed > 0:
        print(f"\nPROBLEMATIC FILES:")
        for result in results:
            if not result['valid'] or result['error']:
                print(f"  - {result['filename']}: {result.get('error', 'Validation failed')}")
    
    return results

if __name__ == "__main__":
    test_all_credit_notes()