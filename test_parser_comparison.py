import os
import sys
import json
import PyPDF2

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import both parsers
from improved_tiktok_parser import parse_tiktok_invoice as parse_improved
from final_corrected_tiktok_parser import parse_tiktok_invoice as parse_final

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

def test_parser(parser_func, parser_name, text_content, filename):
    """Test a parser function and return results"""
    print(f"\n{'='*60}")
    print(f"Testing {parser_name} with {filename}")
    print(f"{'='*60}")
    
    try:
        results = parser_func(text_content, filename)
        print(f"[SUCCESS] Parser succeeded - Found {len(results)} records")
        
        for i, record in enumerate(results, 1):
            print(f"\nRecord {i}:")
            print(f"  Invoice Type: {record.get('invoice_type', 'N/A')}")
            print(f"  Line Number: {record.get('line_number', 'N/A')}")
            print(f"  Agency: {record.get('agency', 'N/A')}")
            print(f"  Project ID: {record.get('project_id', 'N/A')}")
            print(f"  Project Name: {record.get('project_name', 'N/A')}")
            print(f"  Objective: {record.get('objective', 'N/A')}")
            print(f"  Period: {record.get('period', 'N/A')}")
            print(f"  Campaign ID: {record.get('campaign_id', 'N/A')}")
            print(f"  Total: {record.get('total', 'N/A')}")
            print(f"  Description: {record.get('description', 'N/A')[:100]}...")
        
        return results
    
    except Exception as e:
        print(f"[FAILED] Parser failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_text_patterns(text_content, filename):
    """Analyze text patterns to understand why parsing might fail"""
    print(f"\n{'='*60}")
    print(f"Text Pattern Analysis for {filename}")
    print(f"{'='*60}")
    
    print(f"Text length: {len(text_content)} characters")
    
    # Check for key patterns
    import re
    
    has_st_pattern = bool(re.search(r'ST\d{10,}', text_content))
    has_pk_pattern = bool(re.search(r'pk\|', text_content))
    has_consumption = 'Consumption Details:' in text_content
    
    print(f"Has ST pattern: {has_st_pattern}")
    print(f"Has pk| pattern: {has_pk_pattern}")
    print(f"Has 'Consumption Details:': {has_consumption}")
    
    # Find ST patterns
    st_matches = re.findall(r'ST\d{10,}', text_content)
    print(f"ST patterns found: {st_matches}")
    
    # Find pk| patterns
    pk_matches = re.findall(r'pk\|[^\n]*', text_content)
    print(f"pk| patterns found: {len(pk_matches)}")
    for i, match in enumerate(pk_matches[:3], 1):
        print(f"  {i}: {match[:100]}...")
    
    # Show first 1000 characters around Consumption Details
    if has_consumption:
        start_pos = text_content.find('Consumption Details:')
        excerpt = text_content[start_pos:start_pos + 1000]
        print(f"\nFirst 1000 chars after 'Consumption Details:':")
        print("-" * 40)
        # Clean the text for display
        safe_excerpt = excerpt.encode('ascii', errors='replace').decode('ascii')
        print(safe_excerpt)
        print("-" * 40)

def main():
    # Test files
    test_files = [
        "Invoice for testing/THTT202502215532-Prakit Holdings Public Company Limited-Invoice.pdf",
        "Invoice for testing/THTT202502215554-Prakit Holdings Public Company Limited-Invoice.pdf"
    ]
    
    for test_file in test_files:
        pdf_path = os.path.join(os.path.dirname(__file__), test_file)
        
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            continue
        
        print(f"\n{'#'*80}")
        print(f"TESTING FILE: {test_file}")
        print(f"{'#'*80}")
        
        # Extract text
        text_content = extract_text_from_pdf(pdf_path)
        if text_content is None:
            continue
        
        filename = os.path.basename(test_file)
        
        # Analyze text patterns first
        analyze_text_patterns(text_content, filename)
        
        # Test improved parser
        improved_results = test_parser(parse_improved, "IMPROVED_TIKTOK_PARSER", text_content, filename)
        
        # Test final corrected parser
        final_results = test_parser(parse_final, "FINAL_CORRECTED_TIKTOK_PARSER", text_content, filename)
        
        # Compare results
        print(f"\n{'='*60}")
        print(f"COMPARISON SUMMARY for {filename}")
        print(f"{'='*60}")
        
        improved_count = len(improved_results) if improved_results else 0
        final_count = len(final_results) if final_results else 0
        
        print(f"Improved parser: {improved_count} records")
        print(f"Final parser: {final_count} records")
        
        if improved_results and final_results:
            print("Both parsers succeeded")
            
            # Compare totals
            improved_total = sum(r.get('total', 0) for r in improved_results)
            final_total = sum(r.get('total', 0) for r in final_results)
            
            print(f"Improved parser total: {improved_total}")
            print(f"Final parser total: {final_total}")
            
        elif improved_results:
            print("Only improved parser succeeded")
        elif final_results:
            print("Only final parser succeeded")
        else:
            print("Both parsers failed")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    main()