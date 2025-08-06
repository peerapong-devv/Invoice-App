import fitz
import re

def analyze_full_pdf_pages(pdf_path):
    """Analyze every page of PDF to find all financial items"""
    
    print(f"=== FULL PDF ANALYSIS: {pdf_path} ===\n")
    
    with fitz.open(pdf_path) as doc:
        print(f"Total pages: {len(doc)}")
        
        all_text = ""
        page_texts = []
        
        # Extract text from each page separately
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            page_texts.append(page_text)
            all_text += page_text + f"\n--- PAGE {page_num + 1} END ---\n"
        
        print(f"Combined text length: {len(all_text)}")
    
    # Clean text
    clean_text = all_text.replace('\u200b', '')
    
    # Find all amounts (positive and negative)
    amount_pattern = r'^(.+?)\s+([-]?[\d,]+\.\d{2})$'
    matches = re.findall(amount_pattern, clean_text, re.MULTILINE)
    
    print(f"\n=== ALL FINANCIAL ITEMS FOUND ===")
    print(f"Total matches: {len(matches)}\n")
    
    # Categorize all items
    campaigns = []
    refunds = []
    fees = []
    totals = []
    other = []
    
    for i, (desc, amount_str) in enumerate(matches, 1):
        desc = desc.strip()
        amount = float(amount_str.replace(',', ''))
        
        # Determine category
        if any(skip in desc.lower() for skip in ['subtotal', 'total', 'gst', 'vat', 'ยอดรวม', 'จำนวนเงิน']):
            totals.append((desc, amount))
            category = "TOTAL"
        elif amount < 0:
            refunds.append((desc, amount))
            category = "REFUND"
        elif any(fee in desc.lower() for fee in ['fee', 'ค่าธรรมเนียม', 'regulatory', 'italian']):
            fees.append((desc, amount))
            category = "FEE"
        elif 'pk|' in desc or len(desc) > 20:
            campaigns.append((desc, amount))
            category = "CAMPAIGN"
        else:
            other.append((desc, amount))
            category = "OTHER"
        
        # Print with encoding safety
        try:
            print(f"{i:2d}. [{category:8s}] {desc[:60]:<60} -> {amount:>12,.2f}")
        except UnicodeEncodeError:
            print(f"{i:2d}. [{category:8s}] [Unicode Text] -> {amount:>12,.2f}")
    
    # Summary by category
    print(f"\n=== SUMMARY BY CATEGORY ===")
    print(f"Campaigns: {len(campaigns)} items, Total: {sum(amount for _, amount in campaigns):,.2f} THB")
    print(f"Refunds: {len(refunds)} items, Total: {sum(amount for _, amount in refunds):,.2f} THB")
    print(f"Fees: {len(fees)} items, Total: {sum(amount for _, amount in fees):,.2f} THB")
    print(f"Totals/Headers: {len(totals)} items")
    print(f"Other: {len(other)} items, Total: {sum(amount for _, amount in other):,.2f} THB")
    
    # Calculate expected total
    net_amount = sum(amount for _, amount in campaigns) + sum(amount for _, amount in refunds) + sum(amount for _, amount in fees)
    print(f"\nCalculated Net: {net_amount:,.2f} THB")
    
    # Show detailed refunds
    if refunds:
        print(f"\n=== DETAILED REFUNDS ===")
        for i, (desc, amount) in enumerate(refunds, 1):
            try:
                print(f"{i}. {desc[:80]} -> {amount:,.2f}")
            except UnicodeEncodeError:
                print(f"{i}. [Unicode Text] -> {amount:,.2f}")
    
    # Show page-by-page breakdown
    print(f"\n=== PAGE-BY-PAGE ANALYSIS ===")
    for page_num, page_text in enumerate(page_texts, 1):
        page_matches = re.findall(amount_pattern, page_text, re.MULTILINE)
        if page_matches:
            print(f"Page {page_num}: {len(page_matches)} financial items")
            # Show first few items from each page
            for j, (desc, amount) in enumerate(page_matches[:3], 1):
                try:
                    print(f"  {j}. {desc[:40]}... -> {amount}")
                except UnicodeEncodeError:
                    print(f"  {j}. [Unicode] -> {amount}")
            if len(page_matches) > 3:
                print(f"  ... and {len(page_matches) - 3} more items")
        else:
            print(f"Page {page_num}: No financial items")
    
    return {
        'campaigns': campaigns,
        'refunds': refunds,
        'fees': fees,
        'totals': totals,
        'other': other,
        'calculated_total': net_amount
    }

# Analyze the specific invoice
result = analyze_full_pdf_pages("Invoice for testing/5297692787.pdf")

# Also check the known good invoice for comparison
print("\n" + "="*80 + "\n")
result2 = analyze_full_pdf_pages("Invoice for testing/5298248238.pdf")