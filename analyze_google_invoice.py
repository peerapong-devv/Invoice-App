import fitz  # PyMuPDF
import json
import re

def analyze_google_invoice(pdf_path):
    """Extract and analyze Google invoice structure"""
    
    with fitz.open(pdf_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
    
    print("=== GOOGLE INVOICE ANALYSIS ===")
    print(f"File: {pdf_path}")
    print(f"Total text length: {len(full_text)}")
    print("\n=== FIRST 2000 CHARACTERS ===")
    try:
        print(full_text[:2000])
    except UnicodeEncodeError:
        print(full_text[:2000].encode('ascii', 'replace').decode('ascii'))
    print("\n=== SEARCHING FOR PATTERNS ===")
    
    # Look for AP pattern (pk|...)
    ap_pattern = r"pk\|[^\n]+[\d,]+\.\d{2}"
    ap_matches = re.findall(ap_pattern, full_text, re.MULTILINE)
    
    if ap_matches:
        print(f"\nFound {len(ap_matches)} AP entries:")
        for i, match in enumerate(ap_matches[:5], 1):
            try:
                print(f"{i}. {match}")
            except UnicodeEncodeError:
                print(f"{i}. {match.encode('ascii', 'replace').decode('ascii')}")
    
    # Look for line items with amounts
    line_pattern = r"^(.+?)\s+([\d,]+\.\d{2})$"
    line_matches = re.findall(line_pattern, full_text, re.MULTILINE)
    
    if line_matches:
        print(f"\nFound {len(line_matches)} line items with amounts:")
        for i, (desc, amount) in enumerate(line_matches[:10], 1):
            try:
                if 'pk|' in desc:
                    print(f"{i}. AP: {desc[:100]}... -> {amount}")
                else:
                    print(f"{i}. Non-AP: {desc[:100]}... -> {amount}")
            except UnicodeEncodeError:
                if 'pk|' in desc:
                    print(f"{i}. AP: {desc[:100].encode('ascii', 'replace').decode('ascii')}... -> {amount}")
                else:
                    print(f"{i}. Non-AP: {desc[:100].encode('ascii', 'replace').decode('ascii')}... -> {amount}")
    
    # Check for invoice number
    invoice_match = re.search(r"Invoice number:\s*(\S+)", full_text, re.IGNORECASE)
    if invoice_match:
        print(f"\nInvoice Number: {invoice_match.group(1)}")
    
    # Save sample text for analysis
    output_file = pdf_path.replace('.pdf', '_sample.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_text[:5000])
    print(f"\nSaved first 5000 chars to: {output_file}")

# Analyze Google invoices
google_invoices = [
    "5298248238.pdf",  # AP invoice
    "5300646032.pdf"   # Non-AP invoice
]

for invoice in google_invoices:
    try:
        analyze_google_invoice(invoice)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Error analyzing {invoice}: {e}")