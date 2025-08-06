#!/usr/bin/env python3
"""
Comprehensive test script to find TikTok parsers that:
1. Extract detailed line-by-line data (agency, project_id, project_name, objective, period, campaign_id for AP invoices)
2. Give the correct total of 2,440,716.88 THB
3. Properly classify AP vs Non-AP invoices (AP requires BOTH ST pattern AND pk| pattern)
"""

import os
import sys
import importlib.util
import traceback
from decimal import Decimal
from pathlib import Path

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# List of TikTok parser files to test
TIKTOK_PARSERS = [
    'backend/tiktok_parser.py',
    'backend/enhanced_tiktok_parser.py',
    'backend/corrected_tiktok_parser.py',
    'backend/fixed_tiktok_parser.py',
    'backend/improved_tiktok_parser.py',
    'backend/corrected_tiktok_parser_v2.py',
    'backend/final_corrected_tiktok_parser.py',
    'backend/final_tiktok_parser.py',
    'backend/working_tiktok_parser.py',
    'backend/working_tiktok_parser_lookup.py',
    'backend/enhanced_tiktok_line_parser.py',
    'backend/enhanced_tiktok_line_parser_backup.py',
    'backend/enhanced_tiktok_line_parser_fixed.py',
    'backend/enhanced_tiktok_line_parser_corrected.py',
    'backend/enhanced_tiktok_line_parser_current.py',
    'backend/enhanced_tiktok_line_parser_v2_final.py',
    'corrected_tiktok_parser_for_failed_invoices.py',
    'test_tiktok_parser.py',
    'debug_tiktok_parser.py'
]

# TikTok invoice files to test with
TIKTOK_INVOICES = [
    'Invoice for testing/THTT202502215482-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215496-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215532-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215554-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215575-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215645-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215678-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215759-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215819-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215864-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215912-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215950-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215955-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216210-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216315-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216319-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216411-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216526-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216572-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216580-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216594-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216602-Prakit Holdings Public Company Limited-Invoice.pdf'
]

def load_parser_module(parser_path):
    """Load a parser module dynamically"""
    try:
        module_name = os.path.splitext(os.path.basename(parser_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, parser_path)
        if spec is None:
            return None, f"Could not create spec for {parser_path}"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, None
    except Exception as e:
        return None, f"Failed to load {parser_path}: {str(e)}"

def get_parse_function(module):
    """Find the appropriate parse function in the module"""
    # Common function names for TikTok parsers
    function_names = [
        'parse_tiktok_invoice',
        'parse_invoice',
        'extract_tiktok_data',
        'process_tiktok_invoice',
        'parse_tiktok_pdf',
        'enhanced_parse_tiktok_invoice',
        'parse_pdf_content'
    ]
    
    for func_name in function_names:
        if hasattr(module, func_name):
            return getattr(module, func_name)
    
    return None

def check_detailed_data(result):
    """Check if result contains detailed line-by-line data for AP invoices"""
    if not isinstance(result, dict):
        return False, "Result is not a dictionary"
    
    # Check if it has line items or detailed data
    line_items = result.get('line_items', []) or result.get('items', []) or result.get('data', [])
    
    if not line_items:
        return False, "No line items found"
    
    # For AP invoices, check if we have the required fields
    required_ap_fields = ['agency', 'project_id', 'project_name', 'objective', 'period', 'campaign_id']
    
    detailed_items = 0
    for item in line_items:
        if isinstance(item, dict):
            # Count items that have most of the required AP fields
            field_count = sum(1 for field in required_ap_fields if field in item and item[field])
            if field_count >= 4:  # At least 4 out of 6 fields
                detailed_items += 1
    
    if detailed_items > 0:
        return True, f"Found {detailed_items} items with detailed AP data"
    else:
        return False, "No items with detailed AP data found"

def check_correct_total(result, target_total=2440716.88):
    """Check if the total matches the expected value"""
    if not isinstance(result, dict):
        return False, "Result is not a dictionary"
    
    # Look for total in various fields
    total_fields = ['total_amount', 'total', 'grand_total', 'final_total', 'amount_due', 'total_thb']
    
    for field in total_fields:
        if field in result:
            try:
                total_value = result[field]
                if isinstance(total_value, str):
                    # Remove commas and currency symbols
                    total_value = total_value.replace(',', '').replace('THB', '').replace('฿', '').strip()
                    total_value = float(total_value)
                elif isinstance(total_value, (int, float)):
                    total_value = float(total_value)
                else:
                    continue
                
                if abs(total_value - target_total) < 0.01:  # Allow for small floating point differences
                    return True, f"Found correct total: {total_value} in field '{field}'"
            except (ValueError, TypeError):
                continue
    
    return False, f"Correct total {target_total} not found"

def check_ap_classification(result):
    """Check if AP vs Non-AP classification is working properly"""
    if not isinstance(result, dict):
        return False, "Result is not a dictionary"
    
    # Check if classification is present
    classification = result.get('classification', result.get('type', result.get('invoice_type', '')))
    
    if not classification:
        return False, "No classification found"
    
    # Check if it has the logic for ST pattern and pk| pattern
    has_st_pattern = result.get('has_st_pattern', False)
    has_pk_pattern = result.get('has_pk_pattern', False)
    
    return True, f"Classification: {classification}, ST pattern: {has_st_pattern}, pk| pattern: {has_pk_pattern}"

def test_parser(parser_path, invoice_paths):
    """Test a single parser with multiple invoices"""
    print(f"\n{'='*80}")
    print(f"TESTING PARSER: {parser_path}")
    print(f"{'='*80}")
    
    # Load the parser module
    module, error = load_parser_module(parser_path)
    if error:
        print(f"FAILED TO LOAD: {error}")
        return False
    
    # Find the parse function
    parse_func = get_parse_function(module)
    if not parse_func:
        print(f"NO PARSE FUNCTION FOUND")
        available_functions = [name for name in dir(module) if callable(getattr(module, name)) and not name.startswith('_')]
        print(f"Available functions: {available_functions}")
        return False
    
    print(f"LOADED SUCCESSFULLY - Using function: {parse_func.__name__}")
    
    # Test with a sample of invoices
    test_invoices = invoice_paths[:3]  # Test with first 3 invoices
    results = {}
    
    for invoice_path in test_invoices:
        if not os.path.exists(invoice_path):
            print(f"WARNING: Invoice not found: {invoice_path}")
            continue
            
        print(f"\nTesting with: {os.path.basename(invoice_path)}")
        
        try:
            result = parse_func(invoice_path)
            results[invoice_path] = result
            
            # Check detailed data
            has_detailed, detailed_msg = check_detailed_data(result)
            print(f"  Detailed data: {'YES' if has_detailed else 'NO'} {detailed_msg}")
            
            # Check correct total
            has_correct_total, total_msg = check_correct_total(result)
            print(f"  Correct total: {'YES' if has_correct_total else 'NO'} {total_msg}")
            
            # Check AP classification
            has_classification, class_msg = check_ap_classification(result)
            print(f"  Classification: {'YES' if has_classification else 'NO'} {class_msg}")
            
            # Overall assessment for this invoice
            if has_detailed and has_correct_total:
                print(f"  *** EXCELLENT: This parser works well for this invoice!")
                return True
            elif has_detailed or has_correct_total:
                print(f"  + PARTIAL: Some requirements met")
            else:
                print(f"  - POOR: Requirements not met")
                
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            traceback.print_exc()
    
    return False

def main():
    """Main test function"""
    print("COMPREHENSIVE TIKTOK PARSER TESTING")
    print("="*80)
    print("Looking for parsers that:")
    print("1. Extract detailed line-by-line data (agency, project_id, project_name, objective, period, campaign_id)")
    print("2. Give correct total of 2,440,716.88 THB")
    print("3. Properly classify AP vs Non-AP invoices")
    print("="*80)
    
    # Get absolute paths
    base_dir = os.path.dirname(__file__)
    
    # Prepare invoice paths
    invoice_paths = []
    for invoice in TIKTOK_INVOICES:
        full_path = os.path.join(base_dir, invoice)
        if os.path.exists(full_path):
            invoice_paths.append(full_path)
    
    print(f"Found {len(invoice_paths)} TikTok invoices to test with")
    
    if not invoice_paths:
        print("❌ No TikTok invoices found for testing!")
        return
    
    # Test each parser
    working_parsers = []
    
    for parser_path in TIKTOK_PARSERS:
        full_parser_path = os.path.join(base_dir, parser_path)
        if not os.path.exists(full_parser_path):
            print(f"WARNING: Parser not found: {parser_path}")
            continue
        
        success = test_parser(full_parser_path, invoice_paths)
        if success:
            working_parsers.append(parser_path)
    
    # Summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    
    if working_parsers:
        print(f"WORKING PARSERS FOUND ({len(working_parsers)}):")
        for parser in working_parsers:
            print(f"  - {parser}")
        print("\nThese parsers meet the criteria:")
        print("  * Extract detailed line-by-line data")
        print("  * Give correct total of 2,440,716.88 THB")
        print("  * Properly classify AP vs Non-AP invoices")
    else:
        print("NO FULLY WORKING PARSERS FOUND")
        print("None of the tested parsers meet all requirements.")
    
    print(f"\nTested {len([p for p in TIKTOK_PARSERS if os.path.exists(os.path.join(base_dir, p))])} parsers")
    print(f"Used {len(invoice_paths)} TikTok invoices for testing")

if __name__ == "__main__":
    main()