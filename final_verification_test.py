#!/usr/bin/env python3
"""
Final verification test to confirm the AP files with validation differences are fixed
"""

import os
import sys
import fitz

# Add backend directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import parse_invoice_text

def final_verification_test():
    """Test the 4 problematic files and verify they now have correct validation differences"""
    
    problem_files = [
        ("5297830454.pdf", 1774),  # Expected diff: 1,774 THB
        ("5298134610.pdf", 1400),  # Expected diff: 1,400 THB
        ("5298157309.pdf", 1898),  # Expected diff: 1,898 THB  
        ("5298361576.pdf", 968)    # Expected diff: 968 THB
    ]
    
    print("FINAL VERIFICATION TEST")
    print("="*60)
    print("Testing the 4 AP files with large validation differences")
    print("Expected outcome: All files should now have correct validation differences")
    print("="*60)
    
    all_fixed = True
    
    for filename, expected_diff in problem_files:
        file_path = os.path.join("Invoice for testing", filename)
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {filename}")
            all_fixed = False
            continue
        
        try:
            # Extract text
            with fitz.open(file_path) as doc:
                full_text = "\n".join(page.get_text() for page in doc)
            
            # Parse using updated logic
            records = parse_invoice_text(full_text, filename)
            
            if not records:
                print(f"❌ {filename}: No records parsed")
                all_fixed = False
                continue
            
            # Calculate validation difference (campaign_charges vs invoice_total)
            campaign_total = sum(r.get('total', 0) for r in records if r.get('item_type') == 'Campaign')
            invoice_total = records[0].get('invoice_total')
            
            if invoice_total is None:
                print(f"❌ {filename}: No invoice total found")
                all_fixed = False
                continue
            
            actual_validation_diff = abs(campaign_total - invoice_total)
            difference_from_expected = abs(actual_validation_diff - expected_diff)
            
            print(f"\n{filename}:")
            print(f"  Expected validation difference: {expected_diff} THB")
            print(f"  Actual validation difference: {actual_validation_diff:.2f} THB")
            print(f"  Difference from expected: {difference_from_expected:.2f} THB")
            print(f"  Invoice total: {invoice_total:,.2f} THB")
            print(f"  Campaign charges: {campaign_total:,.2f} THB")
            print(f"  Records parsed: {len(records)}")
            
            # Check if it's within acceptable tolerance (1 THB)
            if difference_from_expected <= 1.0:
                print(f"  ✅ Status: FIXED!")
            else:
                print(f"  ❌ Status: Still needs work")
                all_fixed = False
            
        except Exception as e:
            print(f"❌ {filename}: Error during processing - {e}")
            all_fixed = False
    
    print(f"\n{'='*60}")
    if all_fixed:
        print("🎉 SUCCESS: All 4 problematic AP files have been fixed!")
        print("✅ Validation differences now match expected values")
        print("✅ Parser correctly handles mixed invoices with charges and refunds")
        print("✅ Invoice totals are correctly detected using frequency analysis")
    else:
        print("❌ Some files still need work")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    final_verification_test()