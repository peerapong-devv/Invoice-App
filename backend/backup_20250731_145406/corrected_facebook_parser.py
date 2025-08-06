#!/usr/bin/env python3

import re
from collections import Counter

def parse_facebook_invoice_corrected(text_content: str, filename: str):
    """
    Corrected Facebook invoice parser that extracts INVOICE TOTAL, not campaign details
    """
    
    lines = text_content.split('\n')
    
    # Base fields
    base_fields = {
        'platform': 'Facebook',
        'filename': filename
    }
    
    # Extract invoice info
    for line in lines:
        if 'Invoice #:' in line:
            invoice_match = re.search(r'Invoice #:\s*(\d+)', line)
            if invoice_match:
                base_fields['invoice_id'] = invoice_match.group(1)
        elif 'Invoice Date:' in line:
            date_match = re.search(r'Invoice Date:\s*([^\s]+)', line)
            if date_match:
                base_fields['invoice_date'] = date_match.group(1)
    
    # Detect invoice type
    has_st_marker = '[ST]' in text_content
    invoice_type = "AP" if has_st_marker else "Non-AP"
    
    print(f"[DEBUG] Facebook {filename}: Type={invoice_type}, Has [ST]={has_st_marker}")
    
    # Find INVOICE TOTAL - the correct approach
    invoice_total = find_facebook_invoice_total(lines, filename)
    
    if invoice_total > 0:
        # Create single record with invoice total
        record = {
            **base_fields,
            'invoice_type': invoice_type,
            'campaign_name': f"Facebook Invoice {base_fields.get('invoice_id', filename)}",
            'description': f"Facebook {invoice_type} Invoice Total",
            'amount': invoice_total
        }
        print(f"[DEBUG] Facebook corrected: Found invoice total {invoice_total:,.2f} THB")
        return [record]
    else:
        print(f"[DEBUG] Facebook corrected: No invoice total found")
        return []

def find_facebook_invoice_total(lines, filename):
    """
    Find the actual invoice total from Facebook invoice
    """
    
    # Strategy 1: Look for explicit "Invoice Total", "Subtotal", etc.
    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()
        
        # Look for total/subtotal lines
        if any(keyword in line_lower for keyword in ['invoice total:', 'subtotal:', 'total amount due']):
            amounts = re.findall(r'[\d,]+\.\d{2}', line_clean)
            if amounts:
                try:
                    return float(amounts[-1].replace(',', ''))  # Take last amount
                except:
                    continue
    
    # Strategy 2: Look for lines that end with amounts and contain "total" keywords
    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()
        
        if ('total' in line_lower or 'subtotal' in line_lower) and not ('campaign' in line_lower):
            amounts = re.findall(r'[\d,]+\.\d{2}', line_clean)
            if amounts:
                try:
                    return float(amounts[-1].replace(',', ''))
                except:
                    continue
    
    # Strategy 3: Frequency analysis - but exclude very large campaign amounts
    all_amounts = []
    for line in lines:
        amounts = re.findall(r'[\d,]+\.\d{2}', line)
        for amount_str in amounts:
            try:
                amount = float(amount_str.replace(',', ''))
                if 100 <= amount <= 10000000:  # Reasonable invoice range
                    all_amounts.append(amount)
            except:
                continue
    
    if all_amounts:
        # Get frequency analysis
        amount_freq = Counter(all_amounts)
        most_common = amount_freq.most_common(5)
        
        print(f"[DEBUG] Amount frequency analysis for {filename}:")
        for amount, count in most_common:
            print(f"[DEBUG]   {amount:,.2f} THB appears {count} times")
        
        # Prefer amounts that appear multiple times (likely totals)
        for amount, count in most_common:
            if count >= 2 and amount < 1000000:  # Multiple appearances, reasonable size
                return amount
        
        # If no repeated amounts, look for reasonable invoice totals
        reasonable_amounts = [amt for amt in all_amounts if 1000 <= amt <= 500000]
        if reasonable_amounts:
            return max(reasonable_amounts)  # Largest reasonable amount
    
    return 0

def test_corrected_parser():
    """Test the corrected parser on problematic files"""
    
    import os
    import PyPDF2
    
    invoice_dir = "../Invoice for testing"
    
    # Test files that had inflated amounts
    test_files = [
        '246541856.pdf',  # Was 62M, should be ~186K
        '246543739.pdf',  # Was 44M, should be ~5M or less
        '246532147.pdf',  # Was 18K, should remain 18K (correct)
    ]
    
    print("TESTING CORRECTED FACEBOOK PARSER")
    print("=" * 50)
    
    for filename in test_files:
        pdf_path = os.path.join(invoice_dir, filename)
        if not os.path.exists(pdf_path):
            continue
            
        print(f"\n[TESTING] {filename}")
        
        # Extract text
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = "\n".join(page.extract_text() for page in pdf_reader.pages)
            
            # Parse with corrected parser
            records = parse_facebook_invoice_corrected(text, filename)
            
            if records:
                total = sum(r.get('amount', 0) for r in records)
                print(f"  Corrected parser result: {total:,.2f} THB")
                print(f"  Records: {len(records)}")
            else:
                print(f"  No records found")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_corrected_parser()