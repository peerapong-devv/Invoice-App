#!/usr/bin/env python3
"""
Simple verification test without unicode issues
"""

import os
import sys
import fitz

# Add backend directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import parse_invoice_text

def simple_verification():
    """Simple verification of the 4 problematic files"""
    
    problem_files = [
        ("5297830454.pdf", 1774),
        ("5298134610.pdf", 1400),
        ("5298157309.pdf", 1898),  
        ("5298361576.pdf", 968)
    ]
    
    print("SIMPLE VERIFICATION TEST")
    print("="*50)
    
    all_fixed = True
    
    for filename, expected_diff in problem_files:
        file_path = os.path.join("Invoice for testing", filename)
        
        try:
            # Extract text
            with fitz.open(file_path) as doc:
                full_text = "\n".join(page.get_text() for page in doc)
            
            # Parse using updated logic
            records = parse_invoice_text(full_text, filename)
            
            # Calculate validation difference
            campaign_total = sum(r.get('total', 0) for r in records if r.get('item_type') == 'Campaign')
            invoice_total = records[0].get('invoice_total')
            actual_validation_diff = abs(campaign_total - invoice_total)
            difference_from_expected = abs(actual_validation_diff - expected_diff)
            
            print(f"\n{filename}:")
            print(f"  Expected: {expected_diff} THB")
            print(f"  Actual: {actual_validation_diff:.2f} THB")
            print(f"  Difference: {difference_from_expected:.2f} THB")
            
            if difference_from_expected <= 1.0:
                print(f"  Status: FIXED")
            else:
                print(f"  Status: NEEDS WORK")
                all_fixed = False
            
        except Exception as e:
            print(f"{filename}: ERROR - {e}")
            all_fixed = False
    
    print(f"\n{'='*50}")
    if all_fixed:
        print("SUCCESS: All files fixed!")
    else:
        print("Some files still need work")

if __name__ == "__main__":
    simple_verification()