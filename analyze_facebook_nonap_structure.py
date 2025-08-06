import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import glob
import fitz  # PyMuPDF
import re

INVOICE_DIR = r'C:\Users\peerapong\invoice-reader-app\Invoice for testing'

# Known AP invoices from the analysis
AP_INVOICES = [
    '246543739.pdf', '246546622.pdf', '246578231.pdf', '246579423.pdf',
    '246727587.pdf', '246738919.pdf', '246774670.pdf', '246791975.pdf', '246865374.pdf'
]

def extract_line_items(text):
    """Extract potential line items from invoice text"""
    lines = text.split('\n')
    line_items = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Skip headers and footers
        skip_words = ['Invoice', 'Date', 'Period', 'Subtotal', 'VAT', 'Total', 'Amount', 
                      'Description', 'Attn', 'Company', 'Address', 'Tax ID', 'Page']
        if any(word in line for word in skip_words):
            continue
            
        # Check if line has a number (potential amount)
        has_number = bool(re.search(r'\d+[,\.]?\d*', line))
        
        # Look for Line# pattern
        line_num_match = re.match(r'^Line#\s*(\d+)', line)
        
        if line_num_match:
            # This is a Line# marker, look for description and amount in next lines
            line_num = line_num_match.group(1)
            desc = ""
            amount = ""
            
            # Look ahead for description and amount
            for j in range(i+1, min(i+10, len(lines))):
                next_line = lines[j].strip()
                if not next_line:
                    continue
                    
                # Check if it's another Line# (stop looking)
                if re.match(r'^Line#\s*\d+', next_line):
                    break
                    
                # Check if it's a pure number (amount)
                if re.match(r'^[\d,]+\.\d{2}$', next_line):
                    amount = next_line
                    break
                elif not amount and next_line:
                    # This is likely the description
                    desc = next_line
            
            line_items.append({
                'line_num': line_num,
                'description': desc,
                'amount': amount,
                'raw': f"Line#{line_num} -> {desc} -> {amount}"
            })
        
        # Also check for simple amount lines (no Line#)
        elif re.match(r'^[\d,]+\.\d{2}$', line):
            # This is a standalone amount
            line_items.append({
                'line_num': None,
                'description': 'Amount only',
                'amount': line,
                'raw': line
            })
    
    return line_items

# Get all Facebook invoices
all_facebook_files = glob.glob(os.path.join(INVOICE_DIR, '246*.pdf')) + \
                    glob.glob(os.path.join(INVOICE_DIR, '247*.pdf'))

# Filter to get only Non-AP invoices
non_ap_files = [f for f in all_facebook_files if os.path.basename(f) not in AP_INVOICES]

print(f"Total Non-AP Facebook invoices: {len(non_ap_files)}")
print(f"\n=== Analyzing Non-AP Invoice Structure ===\n")

# Analyze a sample of Non-AP invoices
sample_size = 10
for idx, file_path in enumerate(non_ap_files[:sample_size]):
    file_name = os.path.basename(file_path)
    print(f"\n{'='*60}")
    print(f"Invoice #{idx+1}: {file_name}")
    print(f"{'='*60}")
    
    with fitz.open(file_path) as doc:
        full_text = "\n".join(page.get_text() for page in doc)
    
    # Extract line items
    line_items = extract_line_items(full_text)
    
    print(f"Found {len(line_items)} line items")
    
    if line_items:
        print("\nLine Items Structure:")
        for item in line_items[:5]:  # Show first 5 items
            if item['line_num']:
                print(f"  Line#{item['line_num']}:")
                print(f"    Description: {item['description'][:80]}...")
                print(f"    Amount: {item['amount']}")
            else:
                print(f"  Standalone amount: {item['amount']}")
    
    # Also show raw text around Line# patterns
    if 'Line#' in full_text:
        print("\nRaw text samples with Line# patterns:")
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            if 'Line#' in line and i < len(lines) - 3:
                print(f"\n  Context around {line.strip()}:")
                for j in range(max(0, i-1), min(len(lines), i+4)):
                    print(f"    [{j}] {lines[j][:80]}")

# Summary analysis
print(f"\n\n{'='*60}")
print("SUMMARY ANALYSIS OF NON-AP FACEBOOK INVOICES")
print(f"{'='*60}")

all_line_items = []
has_line_pattern = 0
has_simple_amounts = 0

for file_path in non_ap_files:
    with fitz.open(file_path) as doc:
        full_text = "\n".join(page.get_text() for page in doc)
    
    line_items = extract_line_items(full_text)
    all_line_items.extend(line_items)
    
    if any(item['line_num'] for item in line_items):
        has_line_pattern += 1
    if any(not item['line_num'] for item in line_items):
        has_simple_amounts += 1

print(f"\nTotal Non-AP invoices analyzed: {len(non_ap_files)}")
print(f"Invoices with Line# pattern: {has_line_pattern}")
print(f"Invoices with simple amounts: {has_simple_amounts}")
print(f"Total line items found: {len(all_line_items)}")

# Show common patterns
print("\nCommon Line Item Patterns:")
line_patterns = [item for item in all_line_items if item['line_num']]
simple_patterns = [item for item in all_line_items if not item['line_num']]

print(f"  Line# patterns: {len(line_patterns)}")
print(f"  Simple amount patterns: {len(simple_patterns)}")

if line_patterns:
    print("\nSample Line# patterns:")
    for item in line_patterns[:5]:
        print(f"  Line#{item['line_num']}: {item['description'][:50]}... -> {item['amount']}")