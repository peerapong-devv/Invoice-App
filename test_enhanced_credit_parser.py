import fitz
import sys
import os
import io

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append('backend')

from enhanced_credit_note_parser import parse_google_credit_note_enhanced, validate_credit_note_totals

def test_enhanced_credit_parser(filename):
    """Test the enhanced credit note parser"""
    print(f"\n{'='*80}")
    print(f"TESTING ENHANCED CREDIT NOTE PARSER: {filename}")
    print('='*80)
    
    filepath = os.path.join("Invoice for testing", filename)
    
    try:
        # Extract text from PDF
        with fitz.open(filepath) as doc:
            text_content = "\n".join(page.get_text() for page in doc)
        
        print(f"Extracted text length: {len(text_content)} characters")
        
        # Parse using enhanced parser
        records = parse_google_credit_note_enhanced(text_content, filename)
        
        print(f"\nParsing Results:")
        print(f"Total records: {len(records)}")
        
        # Validate totals
        validation = validate_credit_note_totals(records)
        print(f"\nValidation: {validation['message']}")
        print(f"Valid: {validation['is_valid']}")
        
        # Show detailed results
        print(f"\nDetailed Results:")
        print("-" * 60)
        
        for i, record in enumerate(records):
            print(f"\nRecord {i+1}:")
            print(f"  Line Number: {record.get('line_number')}")
            print(f"  Amount: {record.get('total')}")
            print(f"  Item Type: {record.get('item_type')}")
            print(f"  Original Invoice: {record.get('original_invoice', 'N/A')}")
            print(f"  Period: {record.get('period', 'N/A')}")
            print(f"  Project Name: {record.get('project_name', 'N/A')}")
            print(f"  Project ID: {record.get('project_id', 'N/A')}")
            print(f"  Objective: {record.get('objective', 'N/A')}")
            print(f"  Campaign ID: {record.get('campaign_id', 'N/A')}")
            
            desc = record.get('description', '')
            if len(desc) > 100:
                desc = desc[:100] + "..."
            print(f"  Description: {desc}")
        
        return records
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        import traceback
        traceback.print_exc()
        return []

# Test credit notes
credit_notes = [
    "5297692790.pdf",   # -6,284.42 (5 invalid activities)
    "5297785878.pdf",   # -1.66 (2 invalid activities)
    "5298281913.pdf",   # -2.87 (2 invalid activities) 
    "5298615229.pdf",   # -442.78 (8 invalid activities)
    "5300482566.pdf"    # -361.13 (4 invalid activities)
]

if __name__ == "__main__":
    # Test first file in detail
    results = test_enhanced_credit_parser(credit_notes[0])
    
    # Quick test others
    print("\n\n" + "="*80)
    print("QUICK TEST OF OTHER CREDIT NOTES:")
    print("="*80)
    
    summary = []
    
    for cn in credit_notes[1:]:
        print(f"\n{cn}:")
        try:
            records = test_enhanced_credit_parser(cn)
            validation = validate_credit_note_totals(records)
            
            summary.append({
                'filename': cn,
                'records': len(records),
                'valid': validation.get('is_valid', False),
                'total': validation.get('invoice_total', 0),
                'sum': validation.get('individual_sum', 0)
            })
            
            print(f"  Records: {len(records)}, Valid: {validation.get('is_valid')}")
            
        except Exception as e:
            print(f"  Error: {e}")
            summary.append({
                'filename': cn,
                'records': 0,
                'valid': False,
                'error': str(e)
            })
    
    # Summary table
    print("\n\n" + "="*80)
    print("SUMMARY OF ALL CREDIT NOTES:")
    print("="*80)
    print(f"{'Filename':<20} {'Records':<8} {'Valid':<6} {'Invoice Total':<15} {'Individual Sum':<15}")
    print("-" * 80)
    
    for item in summary:
        filename = item['filename']
        records = item['records']
        valid = "Yes" if item['valid'] else "No"
        total = item.get('total', 0)
        sum_amt = item.get('sum', 0)
        
        print(f"{filename:<20} {records:<8} {valid:<6} {total:<15.2f} {sum_amt:<15.2f}")