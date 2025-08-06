import os
import sys
import json
import PyPDF2

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import all three parsers
from improved_tiktok_parser import parse_tiktok_invoice as parse_improved
from final_corrected_tiktok_parser import parse_tiktok_invoice as parse_final
from corrected_tiktok_parser_for_failed_invoices import parse_tiktok_invoice as parse_corrected

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None

def test_parser_safe(parser_func, parser_name, text_content, filename):
    """Test a parser function safely and return results"""
    try:
        results = parser_func(text_content, filename)
        return {
            'success': True,
            'records': results,
            'count': len(results),
            'total_amount': sum(r.get('total', 0) for r in results),
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'records': [],
            'count': 0,
            'total_amount': 0,
            'error': str(e)
        }

def main():
    # Test files
    test_files = [
        "Invoice for testing/THTT202502215532-Prakit Holdings Public Company Limited-Invoice.pdf",
        "Invoice for testing/THTT202502215554-Prakit Holdings Public Company Limited-Invoice.pdf"
    ]
    
    parsers = [
        (parse_improved, "IMPROVED_TIKTOK_PARSER"),
        (parse_final, "FINAL_CORRECTED_TIKTOK_PARSER"),
        (parse_corrected, "CORRECTED_PARSER_FOR_FAILED_INVOICES")
    ]
    
    for test_file in test_files:
        pdf_path = os.path.join(os.path.dirname(__file__), test_file)
        
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            continue
        
        print(f"\n{'#'*100}")
        print(f"TESTING FILE: {test_file}")
        print(f"{'#'*100}")
        
        # Extract text
        text_content = extract_text_from_pdf(pdf_path)
        if text_content is None:
            continue
        
        filename = os.path.basename(test_file)
        
        # Test all parsers
        results = {}
        for parser_func, parser_name in parsers:
            print(f"\n{'='*60}")
            print(f"Testing {parser_name}")
            print(f"{'='*60}")
            
            result = test_parser_safe(parser_func, parser_name, text_content, filename)
            results[parser_name] = result
            
            if result['success']:
                print(f"[SUCCESS] Found {result['count']} records, Total: {result['total_amount']}")
                
                for i, record in enumerate(result['records'], 1):
                    desc_safe = record.get('description', 'N/A')
                    if isinstance(desc_safe, str):
                        desc_safe = desc_safe.encode('ascii', errors='replace').decode('ascii')
                    
                    print(f"  Record {i}:")
                    print(f"    Type: {record.get('invoice_type', 'N/A')}")
                    print(f"    Line: {record.get('line_number', 'N/A')}")
                    print(f"    Agency: {record.get('agency', 'N/A')}")
                    print(f"    Project ID: {record.get('project_id', 'N/A')}")
                    print(f"    Project Name: {record.get('project_name', 'N/A')}")
                    print(f"    Objective: {record.get('objective', 'N/A')}")
                    print(f"    Period: {record.get('period', 'N/A')}")
                    print(f"    Campaign ID: {record.get('campaign_id', 'N/A')}")
                    print(f"    Total: {record.get('total', 'N/A')}")
                    print(f"    Description: {desc_safe[:100]}...")
            else:
                print(f"[FAILED] Error: {result['error']}")
        
        # Summary comparison
        print(f"\n{'='*80}")
        print(f"COMPARISON SUMMARY for {filename}")
        print(f"{'='*80}")
        
        for parser_name in results:
            result = results[parser_name]
            status = "SUCCESS" if result['success'] else "FAILED"
            print(f"{parser_name}: {status} - {result['count']} records - Total: {result['total_amount']}")
        
        # Determine the best parser for this file
        successful_parsers = [(name, result) for name, result in results.items() if result['success'] and result['count'] > 0]
        
        if successful_parsers:
            best_parser = max(successful_parsers, key=lambda x: x[1]['count'])
            print(f"\nBest performing parser: {best_parser[0]} with {best_parser[1]['count']} records")
        else:
            print(f"\nNo parser successfully processed this file!")
        
        print("\n" + "="*100)

if __name__ == "__main__":
    main()