import fitz
import sys
import os
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append('backend')

from app import parse_invoice_text

def final_credit_note_test():
    """Final test of all credit notes using updated app.py parser"""
    
    credit_notes = [
        "5297692790.pdf",   # -6,284.42
        "5297785878.pdf",   # -1.66  
        "5298281913.pdf",   # -2.87
        "5298615229.pdf",   # -442.78
        "5300482566.pdf",   # -361.13
        "5301461407.pdf",
        "5302012325.pdf",   # This was the problematic one (regular invoice)
        "5302293067.pdf",
        "5302788327.pdf",
        "5302951835.pdf",
        "5303158396.pdf",
        "5303649115.pdf"
    ]
    
    print("="*100)
    print("FINAL INTEGRATED TEST - All Credit Notes with Updated app.py")
    print("="*100)
    
    results = []
    
    for i, filename in enumerate(credit_notes):
        print(f"\n{i+1:2d}. Testing {filename}...")
        
        try:
            filepath = os.path.join("Invoice for testing", filename)
            
            # Extract text
            with fitz.open(filepath) as doc:
                text_content = "\n".join(page.get_text() for page in doc)
            
            # Parse using updated app.py
            records = parse_invoice_text(text_content, filename)
            
            # Basic validation
            total_amount = sum(r.get('total', 0) for r in records if r.get('total'))
            
            # Store results
            results.append({
                'filename': filename,
                'records': len(records),
                'total_amount': total_amount,
                'credit_notes': len([r for r in records if r.get('item_type') == 'Refund']),
                'campaigns': len([r for r in records if r.get('item_type') == 'Campaign']),
                'error': None
            })
            
            # Quick summary
            refunds = len([r for r in records if r.get('item_type') == 'Refund'])
            campaigns = len([r for r in records if r.get('item_type') == 'Campaign'])
            
            print(f"    ✓ {len(records)} records ({refunds} refunds, {campaigns} campaigns), Total: {total_amount:.2f}")
            
        except Exception as e:
            print(f"    ✗ ERROR - {str(e)}")
            results.append({
                'filename': filename,
                'records': 0,
                'total_amount': 0,
                'credit_notes': 0,
                'campaigns': 0,
                'error': str(e)
            })
    
    # Summary table
    print("\n\n" + "="*100)
    print("FINAL SUMMARY - Integration Test Results")
    print("="*100)
    print(f"{'#':<3} {'Filename':<20} {'Records':<8} {'Refunds':<8} {'Campaigns':<10} {'Total Amount':<13} {'Status'}")
    print("-" * 100)
    
    passed = 0
    failed = 0
    total_credit_amount = 0
    
    for i, result in enumerate(results):
        num = f"{i+1}."
        filename = result['filename']
        records = result['records']
        refunds = result['credit_notes']
        campaigns = result['campaigns']
        amount = result['total_amount']
        
        if result['error']:
            status = f"ERROR"
            failed += 1
        elif records > 0:
            status = "PASS"
            passed += 1
            if amount < 0:  # Credit note
                total_credit_amount += amount
        else:
            status = "FAIL"
            failed += 1
        
        print(f"{num:<3} {filename:<20} {records:<8} {refunds:<8} {campaigns:<10} {amount:<13.2f} {status}")
    
    print("-" * 100)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {len(credit_notes)} files")
    print(f"Total Credit Amount: {total_credit_amount:.2f} THB")
    
    # Show some sample records from first successful credit note
    print(f"\nSAMPLE CREDIT NOTE RECORDS (from first successful file):")
    print("-" * 60)
    
    for result in results:
        if result['records'] > 0 and result['credit_notes'] > 0:
            # Get records from this file
            filename = result['filename']
            filepath = os.path.join("Invoice for testing", filename)
            
            with fitz.open(filepath) as doc:
                text_content = "\n".join(page.get_text() for page in doc)
            
            records = parse_invoice_text(text_content, filename)
            
            print(f"\nFrom {filename} ({len(records)} records):")
            for j, record in enumerate(records[:3]):  # Show first 3
                print(f"  {j+1}. Line: {record.get('line_number')}, "
                      f"Amount: {record.get('total')}, "
                      f"Type: {record.get('item_type')}, "
                      f"Original Invoice: {record.get('original_invoice', 'N/A')}")
            
            if len(records) > 3:
                print(f"  ... and {len(records) - 3} more records")
            break
    
    return results

if __name__ == "__main__":
    final_credit_note_test()