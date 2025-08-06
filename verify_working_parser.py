#!/usr/bin/env python3
"""
Verify the working TikTok parser that achieves the correct total
"""

import os
import sys
import importlib.util

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

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

def test_single_parser(parser_path, function_name):
    """Test a single parser with all TikTok invoices"""
    
    print(f"TESTING PARSER: {os.path.basename(parser_path)}")
    print(f"Function: {function_name}")
    print("="*60)
    
    # Load the parser
    module, error = load_parser_module(parser_path)
    if error:
        print(f"ERROR: {error}")
        return False
    
    if not hasattr(module, function_name):
        print(f"ERROR: Function {function_name} not found")
        return False
    
    parse_func = getattr(module, function_name)
    
    # Get all TikTok invoices
    invoice_dir = "Invoice for testing"
    tiktok_invoices = []
    
    for filename in os.listdir(invoice_dir):
        if filename.startswith("THTT") and filename.endswith(".pdf"):
            tiktok_invoices.append(os.path.join(invoice_dir, filename))
    
    tiktok_invoices.sort()
    print(f"Found {len(tiktok_invoices)} TikTok invoices")
    
    # Process all invoices
    all_results = []
    total_amount = 0
    ap_count = 0
    non_ap_count = 0
    detailed_items = 0
    
    for i, invoice_path in enumerate(tiktok_invoices, 1):
        filename = os.path.basename(invoice_path)
        print(f"\nProcessing {i}/{len(tiktok_invoices)}: {filename}")
        
        try:
            # Extract text
            text_content = extract_text_from_pdf(invoice_path)
            if text_content.startswith("ERROR:"):
                print(f"  Text extraction failed")
                continue
            
            # Parse invoice
            results = parse_func(text_content, filename)
            
            if isinstance(results, list):
                all_results.extend(results)
                
                # Calculate totals
                file_total = 0
                for item in results:
                    if isinstance(item, dict) and 'amount' in item:
                        try:
                            amount = float(item['amount'])
                            file_total += amount
                            total_amount += amount
                        except (ValueError, TypeError):
                            pass
                
                # Count types
                if results and isinstance(results[0], dict):
                    invoice_type = results[0].get('invoice_type', 'Unknown')
                    if invoice_type == 'AP':
                        ap_count += 1
                    elif invoice_type == 'Non-AP':
                        non_ap_count += 1
                    
                    # Count detailed items (with multiple required fields)
                    for item in results:
                        if isinstance(item, dict):
                            field_count = sum(1 for field in ['agency', 'project_id', 'project_name', 'objective'] 
                                            if field in item and item[field] and item[field] != 'Unknown')
                            if field_count >= 2:
                                detailed_items += 1
                
                print(f"  Type: {invoice_type}, Items: {len(results)}, File Total: {file_total:,.2f} THB")
            else:
                print(f"  ERROR: Unexpected result type: {type(results)}")
                
        except Exception as e:
            print(f"  ERROR: {str(e)}")
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Total invoices processed: {len(tiktok_invoices)}")
    print(f"AP invoices: {ap_count}")
    print(f"Non-AP invoices: {non_ap_count}")
    print(f"Total line items: {len(all_results)}")
    print(f"Items with detailed data: {detailed_items}")
    print(f"Grand total: {total_amount:,.2f} THB")
    print(f"Target total: 2,440,716.88 THB")
    print(f"Difference: {abs(total_amount - 2440716.88):,.2f} THB")
    
    # Check success criteria
    correct_total = abs(total_amount - 2440716.88) < 1.0
    has_detailed_data = detailed_items > 0
    proper_classification = ap_count > 0 and non_ap_count > 0
    
    print(f"\nSUCCESS CRITERIA:")
    print(f"  Correct total (2,440,716.88 THB): {'YES' if correct_total else 'NO'}")
    print(f"  Has detailed line-by-line data: {'YES' if has_detailed_data else 'NO'}")
    print(f"  Proper AP/Non-AP classification: {'YES' if proper_classification else 'NO'}")
    
    if correct_total and has_detailed_data and proper_classification:
        print(f"\n*** SUCCESS: This parser meets all requirements! ***")
        return True
    else:
        print(f"\n- PARTIAL: Some requirements not met")
        return False

def main():
    """Main function"""
    base_dir = os.path.dirname(__file__)
    
    # Test the most promising parsers based on the summary
    parsers_to_test = [
        {
            'path': os.path.join(base_dir, 'backend', 'enhanced_tiktok_line_parser_corrected.py'),
            'function': 'parse_tiktok_invoice_detailed'
        },
        {
            'path': os.path.join(base_dir, 'backend', 'enhanced_tiktok_line_parser_v2_final.py'),
            'function': 'parse_tiktok_invoice_detailed'
        },
        {
            'path': os.path.join(base_dir, 'backend', 'enhanced_tiktok_line_parser.py'),
            'function': 'parse_tiktok_invoice_detailed'
        }
    ]
    
    print("VERIFYING WORKING TIKTOK PARSERS")
    print("="*60)
    print("Looking for parsers that:")
    print("1. Extract detailed line-by-line data")
    print("2. Give correct total of 2,440,716.88 THB")
    print("3. Properly classify AP vs Non-AP invoices")
    print("="*60)
    
    working_parsers = []
    
    for parser_info in parsers_to_test:
        if os.path.exists(parser_info['path']):
            success = test_single_parser(parser_info['path'], parser_info['function'])
            if success:
                working_parsers.append(os.path.basename(parser_info['path']))
        else:
            print(f"Parser not found: {parser_info['path']}")
    
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    
    if working_parsers:
        print(f"WORKING PARSERS FOUND ({len(working_parsers)}):")
        for parser in working_parsers:
            print(f"  * {parser}")
    else:
        print("NO FULLY WORKING PARSERS FOUND")

if __name__ == "__main__":
    main()