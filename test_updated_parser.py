#!/usr/bin/env python3
"""
Test script to use the updated parser logic from app.py
"""

import os
import sys
import json
import fitz  # PyMuPDF

# Add backend directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the updated parser from app.py
from app import parse_invoice_text, process_invoice_file

def test_file_with_updated_parser(filename):
    """Test parsing a single file with the updated parser"""
    file_path = os.path.join("Invoice for testing", filename)
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None, 0
    
    print(f"\n{'='*60}")
    print(f"Testing: {filename}")
    print(f"{'='*60}")
    
    try:
        # Extract text
        with fitz.open(file_path) as doc:
            full_text = "\n".join(page.get_text() for page in doc)
        
        if not full_text:
            print("No text extracted!")
            return None, 0
        
        print(f"Text length: {len(full_text)} characters")
        
        # Parse using the updated logic from app.py
        records = parse_invoice_text(full_text, filename)
        
        print(f"Parsed {len(records)} records")
        
        # Calculate total
        total_amount = 0
        for record in records:
            if record.get('total'):
                total_amount += record['total']
        
        print(f"Total parsed amount: {total_amount:,.2f} THB")
        
        # Show records summary
        print(f"\nRecords summary:")
        campaign_total = 0
        refund_total = 0
        
        for i, record in enumerate(records):
            item_type = record.get('item_type', 'Unknown')
            amount = record.get('total', 0)
            
            if item_type == 'Campaign':
                campaign_total += amount
            elif item_type == 'Refund':
                refund_total += amount
            
            print(f"  Record {i+1}: {item_type}, Amount: {amount}, Platform: {record.get('platform')}")
            if record.get('description'):
                desc = record['description'][:100] + "..." if len(record['description']) > 100 else record['description']
                print(f"    Description: {desc}")
        
        print(f"\nTotals by type:")
        print(f"  Campaigns: {campaign_total:,.2f} THB")
        print(f"  Refunds: {refund_total:,.2f} THB")
        print(f"  Net Total: {campaign_total + refund_total:,.2f} THB")
        
        # Show invoice total if available
        if records and records[0].get('invoice_total'):
            invoice_total = records[0]['invoice_total']
            print(f"  Invoice Total: {invoice_total:,.2f} THB")
            difference = abs((campaign_total + refund_total) - invoice_total)
            print(f"  Validation Difference: {difference:,.2f} THB")
        
        return records, total_amount
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

def main():
    """Test the 4 problematic files with updated parser"""
    
    problem_files = [
        ("5297830454.pdf", 1774),  # Expected diff: 1,774 THB
        ("5298134610.pdf", 1400),  # Expected diff: 1,400 THB
        ("5298157309.pdf", 1898),  # Expected diff: 1,898 THB  
        ("5298361576.pdf", 968)    # Expected diff: 968 THB
    ]
    
    results = {}
    
    for filename, expected_diff in problem_files:
        records, total_amount = test_file_with_updated_parser(filename)
        
        results[filename] = {
            'expected_diff': expected_diff,
            'parsed_total': total_amount,
            'record_count': len(records) if records else 0,
            'records': records if records else []
        }
        
        if records:
            # Calculate validation difference if we have invoice total
            if records[0].get('invoice_total'):
                invoice_total = records[0]['invoice_total']
                actual_diff = abs(total_amount - invoice_total)
                results[filename]['actual_diff'] = actual_diff
                results[filename]['invoice_total'] = invoice_total
                
                print(f"Expected validation difference: {expected_diff} THB")
                print(f"Actual validation difference: {actual_diff:,.2f} THB")
                
                if abs(actual_diff - expected_diff) < 100:  # Within 100 THB tolerance
                    print("V Validation difference is close to expected!")
                else:
                    print("X Validation difference differs from expected")
    
    # Summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    for filename, result in results.items():
        print(f"\n{filename}:")
        print(f"  Expected diff: {result['expected_diff']} THB")
        print(f"  Parsed total: {result['parsed_total']:,.2f} THB")
        print(f"  Records: {result['record_count']}")
        if 'actual_diff' in result:
            print(f"  Actual diff: {result['actual_diff']:,.2f} THB")
            print(f"  Invoice total: {result['invoice_total']:,.2f} THB")
            
            diff_from_expected = abs(result['actual_diff'] - result['expected_diff'])
            if diff_from_expected < 100:
                print(f"  Status: FIXED (diff from expected: {diff_from_expected:.2f} THB)")
            else:
                print(f"  Status: NEEDS WORK (diff from expected: {diff_from_expected:.2f} THB)")
    
    # Save results
    with open('updated_parser_test_results.json', 'w', encoding='utf-8') as f:
        # Make records JSON serializable
        serializable_results = {}
        for filename, result in results.items():
            serializable_results[filename] = {
                'expected_diff': result['expected_diff'],
                'parsed_total': result['parsed_total'],
                'record_count': result['record_count'],
                'actual_diff': result.get('actual_diff'),
                'invoice_total': result.get('invoice_total')
            }
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: updated_parser_test_results.json")

if __name__ == "__main__":
    main()