#!/usr/bin/env python3
"""
Examine the detailed data extraction from a TikTok AP invoice
"""

import os
import sys
import importlib.util

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using available library"""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except ImportError:
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except ImportError:
            return f"ERROR: No PDF library available"

def load_parser_module(parser_path):
    """Load a parser module dynamically"""
    try:
        module_name = os.path.splitext(os.path.basename(parser_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, parser_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, None
    except Exception as e:
        return None, f"Failed to load {parser_path}: {str(e)}"

def main():
    """Examine detailed data from AP invoices"""
    
    # Load the working parser
    parser_path = os.path.join(os.path.dirname(__file__), 'backend', 'enhanced_tiktok_line_parser_corrected.py')
    module, error = load_parser_module(parser_path)
    
    if error:
        print(f"Error loading parser: {error}")
        return
    
    parse_func = getattr(module, 'parse_tiktok_invoice_detailed')
    
    # Test with specific AP invoices that showed detailed data
    ap_invoices = [
        'Invoice for testing/THTT202502215554-Prakit Holdings Public Company Limited-Invoice.pdf',
        'Invoice for testing/THTT202502215575-Prakit Holdings Public Company Limited-Invoice.pdf',
        'Invoice for testing/THTT202502216411-Prakit Holdings Public Company Limited-Invoice.pdf'
    ]
    
    for invoice_file in ap_invoices:
        if not os.path.exists(invoice_file):
            print(f"Invoice not found: {invoice_file}")
            continue
            
        print(f"\n{'='*80}")
        print(f"EXAMINING: {os.path.basename(invoice_file)}")
        print(f"{'='*80}")
        
        # Extract text and parse
        text_content = extract_text_from_pdf(invoice_file)
        if text_content.startswith("ERROR:"):
            print(text_content)
            continue
            
        filename = os.path.basename(invoice_file)
        results = parse_func(text_content, filename)
        
        if not isinstance(results, list):
            print(f"Unexpected result type: {type(results)}")
            continue
            
        print(f"Number of line items: {len(results)}")
        print(f"Invoice type: {results[0].get('invoice_type', 'Unknown') if results else 'No results'}")
        
        # Show detailed data for each line item
        total_amount = 0
        detailed_count = 0
        
        for i, item in enumerate(results[:10], 1):  # Show first 10 items
            if isinstance(item, dict):
                print(f"\nLine {i}:")
                
                # Core fields
                for field in ['agency', 'project_id', 'project_name', 'objective', 'period', 'campaign_id', 'amount']:
                    value = item.get(field, 'Not found')
                    if value and value != 'Unknown':
                        print(f"  {field}: {value}")
                    
                # Count items with detailed data
                field_count = sum(1 for field in ['agency', 'project_id', 'project_name', 'objective'] 
                                if field in item and item[field] and item[field] != 'Unknown')
                if field_count >= 2:
                    detailed_count += 1
                    
                # Add to total
                if 'amount' in item:
                    try:
                        amount = float(item['amount'])
                        total_amount += amount
                    except (ValueError, TypeError):
                        pass
        
        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more items")
            
        print(f"\nSUMMARY:")
        print(f"  Total items: {len(results)}")
        print(f"  Items with detailed data: {detailed_count}")
        print(f"  Invoice total: {total_amount:,.2f} THB")
        
        # Check classification
        has_st = 'ST' in text_content
        has_pk = 'pk|' in text_content
        print(f"  Has ST patterns: {has_st}")
        print(f"  Has pk| patterns: {has_pk}")
        print(f"  Classification logic: AP = {has_st and has_pk}")

if __name__ == "__main__":
    main()