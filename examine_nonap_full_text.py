import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import fitz  # PyMuPDF

INVOICE_DIR = r'C:\Users\peerapong\invoice-reader-app\Invoice for testing'

# Examine a specific Non-AP invoice in full detail
def examine_full_invoice(filename):
    file_path = os.path.join(INVOICE_DIR, filename)
    if not os.path.exists(file_path):
        print(f"File not found: {filename}")
        return
    
    print(f"{'='*80}")
    print(f"FULL TEXT ANALYSIS: {filename}")
    print(f"{'='*80}")
    
    with fitz.open(file_path) as doc:
        full_text = "\n".join(page.get_text() for page in doc)
    
    lines = full_text.split('\n')
    
    print(f"Total lines: {len(lines)}")
    print(f"Total characters: {len(full_text)}")
    print(f"\nFull text with line numbers:")
    
    for i, line in enumerate(lines):
        print(f"{i:3d}: {repr(line)}")

# Examine several Non-AP invoices
test_invoices = ['246530629.pdf', '247036228.pdf', '246532147.pdf']

for invoice in test_invoices:
    if os.path.exists(os.path.join(INVOICE_DIR, invoice)):
        examine_full_invoice(invoice)
        print("\n" + "="*100 + "\n")
    else:
        print(f"Invoice {invoice} not found")