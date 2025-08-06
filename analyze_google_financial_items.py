import fitz
import re

def analyze_google_financial_structure(pdf_path):
    """Analyze Google invoice to find all financial items including refunds and fees"""
    
    with fitz.open(pdf_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
    
    # Clean text
    full_text = full_text.replace('\u200b', '')
    
    print(f"=== Analyzing: {pdf_path} ===\n")
    
    # Find invoice total from first page
    total_patterns = [
        r'฿([\d,]+\.\d{2})\s*ครบกำหนด',  # Thai pattern
        r'Total.*?฿([\d,]+\.\d{2})',
        r'จำนวนเงินรวม.*?฿([\d,]+\.\d{2})'
    ]
    
    invoice_total = None
    for pattern in total_patterns:
        match = re.search(pattern, full_text)
        if match:
            invoice_total = float(match.group(1).replace(',', ''))
            print(f"Invoice Total: {invoice_total:,.2f} THB")
            break
    
    # Find all line items with amounts (positive and negative)
    print("\nAll Financial Items:")
    print("-" * 50)
    
    # Pattern for any line ending with amount
    amount_pattern = r'^(.+?)\s+([-]?[\d,]+\.\d{2})$'
    matches = re.findall(amount_pattern, full_text, re.MULTILINE)
    
    line_items = []
    refunds = []
    fees = []
    other_items = []
    
    for desc, amount_str in matches:
        desc = desc.strip()
        amount = float(amount_str.replace(',', ''))
        
        # Skip subtotals and headers
        if any(skip in desc.lower() for skip in ['subtotal', 'total', 'gst', 'vat', 'หน้า', 'page']):
            continue
        
        # Categorize items
        if amount < 0:
            refunds.append({'description': desc, 'amount': amount})
            print(f"REFUND: {desc[:60]}... -> {amount:,.2f}")
        elif 'fee' in desc.lower() or 'ค่าธรรมเนียม' in desc:
            fees.append({'description': desc, 'amount': amount})
            print(f"FEE: {desc[:60]}... -> {amount:,.2f}")
        elif 'pk|' in desc or len(desc) > 20:  # Likely campaign item
            line_items.append({'description': desc, 'amount': amount})
            print(f"CAMPAIGN: {desc[:60]}... -> {amount:,.2f}")
        else:
            other_items.append({'description': desc, 'amount': amount})
            print(f"OTHER: {desc[:60]}... -> {amount:,.2f}")
    
    # Calculate sums
    campaign_sum = sum(item['amount'] for item in line_items)
    refund_sum = sum(item['amount'] for item in refunds)
    fee_sum = sum(item['amount'] for item in fees)
    other_sum = sum(item['amount'] for item in other_items)
    calculated_total = campaign_sum + refund_sum + fee_sum + other_sum
    
    print(f"\n=== SUMMARY ===")
    print(f"Campaign items: {len(line_items)} items, {campaign_sum:,.2f} THB")
    print(f"Refunds: {len(refunds)} items, {refund_sum:,.2f} THB")
    print(f"Fees: {len(fees)} items, {fee_sum:,.2f} THB")
    print(f"Other: {len(other_items)} items, {other_sum:,.2f} THB")
    print(f"Calculated Total: {calculated_total:,.2f} THB")
    
    if invoice_total:
        difference = abs(calculated_total - invoice_total)
        print(f"Invoice Total: {invoice_total:,.2f} THB")
        print(f"Difference: {difference:,.2f} THB")
        if difference < 0.01:
            print("✓ Totals match!")
        else:
            print("✗ Totals don't match - need to find missing items")
    
    return {
        'invoice_total': invoice_total,
        'line_items': line_items,
        'refunds': refunds,
        'fees': fees,
        'other_items': other_items,
        'calculated_total': calculated_total
    }

# Test on a few Google invoices
test_files = [
    "Invoice for testing/5298248238.pdf",  # Known AP
    "Invoice for testing/5300646032.pdf",  # Known Non-AP
    "Invoice for testing/5297692787.pdf",  # Another AP
]

for pdf_file in test_files:
    try:
        result = analyze_google_financial_structure(pdf_file)
        print("\n" + "="*70 + "\n")
    except Exception as e:
        print(f"Error analyzing {pdf_file}: {e}")
        print("\n" + "="*70 + "\n")