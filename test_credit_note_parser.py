import fitz
import sys
import os
import io

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append('backend')

from perfect_google_parser import parse_google_invoice_perfect, validate_perfect_totals

def test_credit_note(filename):
    """Test parser with a credit note file"""
    print(f"\n{'='*60}")
    print(f"Testing Credit Note: {filename}")
    print('='*60)
    
    filepath = os.path.join("Invoice for testing", filename)
    
    # Extract text from PDF
    try:
        with fitz.open(filepath) as doc:
            text_content = "\n".join(page.get_text() for page in doc)
        
        print(f"\nExtracted text length: {len(text_content)} characters")
        
        # Look for credit note indicators
        credit_indicators = ["credit note", "ใบลดหนี้", "คืนเงิน", "-฿", "นี่เป็นเครดิต", "โปรดอย่าชำระเงิน"]
        found_indicators = []
        
        for indicator in credit_indicators:
            if indicator in text_content or indicator in text_content.lower():
                found_indicators.append(indicator)
        
        if found_indicators:
            print(f"\nFound credit note indicators: {found_indicators}")
        
        # Parse the invoice
        records = parse_google_invoice_perfect(text_content, filename)
        
        # Validate totals
        validation = validate_perfect_totals(records)
        
        print(f"\nParsing Results:")
        print(f"Total records: {len(records)}")
        
        # Group by type
        refunds = [r for r in records if r.get('item_type') == 'Refund']
        campaigns = [r for r in records if r.get('item_type') == 'Campaign']
        fees = [r for r in records if r.get('item_type') == 'Fee']
        
        print(f"Refunds: {len(refunds)}")
        print(f"Campaigns: {len(campaigns)}")
        print(f"Fees: {len(fees)}")
        
        print(f"\nValidation: {validation['message']}")
        if validation.get('invoice_total'):
            print(f"Invoice Total: {validation['invoice_total']}")
        
        # Show refund details
        if refunds:
            print("\nRefund Details:")
            for i, refund in enumerate(refunds[:5]):  # Show first 5 refunds
                print(f"  {i+1}. Amount: {refund.get('total')}, Description: {refund.get('description', 'N/A')[:50]}...")
        
        # Look for specific Thai text patterns in credit notes
        print("\n" + "-"*40)
        print("Looking for Thai credit note text patterns...")
        
        # Search for the specific Thai text that indicates invalid activity
        if "กิจกรรมที่ไม่ถูกต้อง" in text_content:
            print("Found: 'กิจกรรมที่ไม่ถูกต้อง' (Invalid activity)")
            
            # Find all occurrences
            lines = text_content.split('\n')
            invalid_activities = []
            
            for i, line in enumerate(lines):
                if "กิจกรรมที่ไม่ถูกต้อง" in line:
                    # Get surrounding lines for context
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    context = '\n'.join(lines[start:end])
                    invalid_activities.append(context)
            
            print(f"\nFound {len(invalid_activities)} invalid activity entries")
            if invalid_activities:
                print("\nFirst invalid activity context:")
                print(invalid_activities[0])
        
        return records
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        import traceback
        traceback.print_exc()
        return []

# Test the first credit note
if __name__ == "__main__":
    credit_notes = [
        "5297692790.pdf",
        "5297785878.pdf",
        "5298281913.pdf",
        "5298615229.pdf",
        "5300482566.pdf"
    ]
    
    # Test first file in detail
    test_credit_note(credit_notes[0])
    
    # Quick test others
    print("\n\n" + "="*60)
    print("Quick test of other credit notes:")
    print("="*60)
    
    for cn in credit_notes[1:]:
        print(f"\n{cn}:")
        try:
            filepath = os.path.join("Invoice for testing", cn)
            with fitz.open(filepath) as doc:
                text = "\n".join(page.get_text() for page in doc)
            
            # Check for negative amounts
            import re
            neg_amounts = re.findall(r'-฿[\d,]+\.\d{2}', text)
            if neg_amounts:
                print(f"  Found negative amounts: {neg_amounts[:3]}...")
            
            # Check for invalid activity
            if "กิจกรรมที่ไม่ถูกต้อง" in text:
                count = text.count("กิจกรรมที่ไม่ถูกต้อง")
                print(f"  Found {count} 'invalid activity' entries")
                
        except Exception as e:
            print(f"  Error: {e}")