#!/usr/bin/env python3
"""
Targeted test for specific TikTok parsers that appear to have the right functions
"""

import os
import sys
import importlib.util
import traceback
from decimal import Decimal

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Target promising parsers with their specific function names
PROMISING_PARSERS = [
    {
        'path': 'backend/working_tiktok_parser.py',
        'function': 'parse_tiktok_invoice_working'
    },
    {
        'path': 'backend/enhanced_tiktok_line_parser_v2_final.py',
        'function': 'parse_tiktok_invoice_detailed'
    },
    {
        'path': 'backend/enhanced_tiktok_line_parser.py',
        'function': 'parse_tiktok_invoice_detailed'
    },
    {
        'path': 'backend/enhanced_tiktok_line_parser_corrected.py',
        'function': 'parse_tiktok_invoice_detailed'
    },
    {
        'path': 'backend/working_tiktok_parser_lookup.py',
        'function': 'parse_tiktok_invoice_lookup'
    }
]

# Sample TikTok invoices
SAMPLE_INVOICES = [
    'Invoice for testing/THTT202502215482-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502215575-Prakit Holdings Public Company Limited-Invoice.pdf',
    'Invoice for testing/THTT202502216594-Prakit Holdings Public Company Limited-Invoice.pdf'
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

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber (assuming it's available)"""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except ImportError:
        print("pdfplumber not available, trying PyPDF2...")
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except ImportError:
            return f"ERROR: No PDF library available to extract text from {pdf_path}"

def check_detailed_data(result):
    """Check if result contains detailed line-by-line data for AP invoices"""
    if not isinstance(result, list):
        return False, "Result is not a list"
    
    if not result:
        return False, "Empty result list"
    
    # Count items with detailed AP fields
    required_ap_fields = ['agency', 'project_id', 'project_name', 'objective', 'period', 'campaign_id']
    
    detailed_items = 0
    for item in result:
        if isinstance(item, dict):
            # Count items that have most of the required AP fields
            field_count = sum(1 for field in required_ap_fields if field in item and item[field])
            if field_count >= 3:  # At least 3 out of 6 fields
                detailed_items += 1
    
    if detailed_items > 0:
        return True, f"Found {detailed_items} items with detailed AP data (out of {len(result)} total)"
    else:
        return False, "No items with detailed AP data found"

def check_correct_total(result, target_total=2440716.88):
    """Check if the total matches the expected value"""
    if not isinstance(result, list):
        return False, "Result is not a list"
    
    # Sum all amounts in the result
    total_amount = 0
    amount_count = 0
    
    for item in result:
        if isinstance(item, dict) and 'amount' in item:
            try:
                amount = item['amount']
                if isinstance(amount, str):
                    # Remove commas and currency symbols
                    amount = amount.replace(',', '').replace('THB', '').replace('฿', '').strip()
                    amount = float(amount)
                elif isinstance(amount, (int, float)):
                    amount = float(amount)
                else:
                    continue
                    
                total_amount += amount
                amount_count += 1
            except (ValueError, TypeError):
                continue
    
    if amount_count > 0 and abs(total_amount - target_total) < 0.01:
        return True, f"Correct total: {total_amount:.2f} from {amount_count} items"
    else:
        return False, f"Incorrect total: {total_amount:.2f} from {amount_count} items (expected {target_total})"

def test_parser(parser_info, pdf_path):
    """Test a specific parser with a PDF file"""
    parser_path = parser_info['path']
    function_name = parser_info['function']
    
    print(f"\n{'='*60}")
    print(f"TESTING: {os.path.basename(parser_path)}")
    print(f"Function: {function_name}")
    print(f"Invoice: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")
    
    # Load the parser module
    base_dir = os.path.dirname(__file__)
    full_parser_path = os.path.join(base_dir, parser_path)
    
    if not os.path.exists(full_parser_path):
        print("PARSER NOT FOUND")
        return False
        
    module, error = load_parser_module(full_parser_path)
    if error:
        print(f"FAILED TO LOAD: {error}")
        return False
    
    # Get the specific function
    if not hasattr(module, function_name):
        print(f"FUNCTION {function_name} NOT FOUND")
        available = [name for name in dir(module) if callable(getattr(module, name)) and not name.startswith('_')]
        print(f"Available functions: {available}")
        return False
    
    parse_func = getattr(module, function_name)
    
    # Extract text from PDF
    text_content = extract_text_from_pdf(pdf_path)
    if text_content.startswith("ERROR:"):
        print(text_content)
        return False
    
    filename = os.path.basename(pdf_path)
    
    try:
        # Call the parser function
        result = parse_func(text_content, filename)
        
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
        
        # Check detailed data
        has_detailed, detailed_msg = check_detailed_data(result)
        print(f"Detailed data: {'YES' if has_detailed else 'NO'} - {detailed_msg}")
        
        # Check correct total
        has_correct_total, total_msg = check_correct_total(result)
        print(f"Correct total: {'YES' if has_correct_total else 'NO'} - {total_msg}")
        
        # Show sample data
        if isinstance(result, list) and result:
            print(f"\nSample item:")
            sample = result[0]
            if isinstance(sample, dict):
                for key, value in list(sample.items())[:10]:  # Show first 10 fields
                    print(f"  {key}: {value}")
            else:
                print(f"  {sample}")
        
        # Overall assessment
        if has_detailed and has_correct_total:
            print("\n*** EXCELLENT: This parser meets all requirements! ***")
            return True
        elif has_detailed or has_correct_total:
            print("\n+ PARTIAL: Some requirements met")
        else:
            print("\n- POOR: Requirements not met")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
    
    return False

def main():
    """Main test function"""
    print("TARGETED TIKTOK PARSER TESTING")
    print("="*60)
    print("Testing specific promising parsers for:")
    print("1. Detailed line-by-line data extraction")
    print("2. Correct total of 2,440,716.88 THB")
    print("="*60)
    
    base_dir = os.path.dirname(__file__)
    
    # Prepare invoice paths
    pdf_paths = []
    for invoice in SAMPLE_INVOICES:
        full_path = os.path.join(base_dir, invoice)
        if os.path.exists(full_path):
            pdf_paths.append(full_path)
        else:
            print(f"WARNING: Invoice not found: {invoice}")
    
    if not pdf_paths:
        print("ERROR: No TikTok invoices found for testing!")
        return
    
    print(f"Testing with {len(pdf_paths)} invoices")
    
    # Test each promising parser
    working_parsers = []
    
    for parser_info in PROMISING_PARSERS:
        # Test with first invoice only for initial assessment
        pdf_path = pdf_paths[0]
        success = test_parser(parser_info, pdf_path)
        
        if success:
            working_parsers.append(parser_info['path'])
            print(f"\n*** FOUND WORKING PARSER: {parser_info['path']} ***")
            
            # Test with all invoices to verify consistency
            print(f"\nTesting {parser_info['path']} with all invoices...")
            for pdf_path in pdf_paths[1:]:  # Test remaining invoices
                test_parser(parser_info, pdf_path)
    
    # Summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    if working_parsers:
        print(f"WORKING PARSERS FOUND ({len(working_parsers)}):")
        for parser in working_parsers:
            print(f"  * {parser}")
        print("\nThese parsers meet the criteria:")
        print("  * Extract detailed line-by-line data")
        print("  * Give correct total of 2,440,716.88 THB")
    else:
        print("NO FULLY WORKING PARSERS FOUND")
    
    print(f"\nTested {len(PROMISING_PARSERS)} promising parsers")
    print(f"Used {len(pdf_paths)} TikTok invoices")

if __name__ == "__main__":
    main()