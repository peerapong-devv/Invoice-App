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

def analyze_invoice_structure(file_path):
    """Analyze the structure of a single invoice in detail"""
    with fitz.open(file_path) as doc:
        full_text = "\n".join(page.get_text() for page in doc)
    
    lines = full_text.split('\n')
    
    # Find where line items start (after headers)
    line_item_start = -1
    for i, line in enumerate(lines):
        if 'Line#' in line and 'Description' in lines[i] or (i+1 < len(lines) and 'Description' in lines[i+1]):
            line_item_start = i + 2  # Skip the header row
            break
    
    # Find where line items end (before totals)
    line_item_end = len(lines)
    for i in range(line_item_start, len(lines)):
        if any(word in lines[i] for word in ['Subtotal', 'VAT', 'Coupon']):
            line_item_end = i
            break
    
    # Extract line items between start and end
    line_items = []
    if line_item_start > 0:
        i = line_item_start
        while i < line_item_end:
            line = lines[i].strip()
            
            # Look for patterns that indicate a line item
            # Pattern 1: Line starting with a number (Line number)
            # Pattern 2: Amount pattern (numbers with commas and decimals)
            
            if line and not any(skip in line for skip in ['Page', 'of', 'Invoice']):
                # Check if this could be a line number
                line_num_match = re.match(r'^(\d+)$', line)
                if line_num_match:
                    # Found a line number, look for description and amount
                    item = {'line_num': line_num_match.group(1), 'description': '', 'amount': ''}
                    
                    # Look ahead for description and amount
                    j = i + 1
                    while j < line_item_end and j < i + 10:
                        next_line = lines[j].strip()
                        
                        # Check if it's an amount
                        if re.match(r'^[\d,]+\.\d{2}$', next_line):
                            item['amount'] = next_line
                            break
                        elif next_line and not re.match(r'^\d+$', next_line):
                            # It's likely a description
                            if item['description']:
                                item['description'] += ' ' + next_line
                            else:
                                item['description'] = next_line
                        
                        j += 1
                    
                    if item['amount']:  # Only add if we found an amount
                        line_items.append(item)
                        i = j  # Skip processed lines
                
                # Check for amount-only lines
                elif re.match(r'^[\d,]+\.\d{2}$', line):
                    # Look back for a possible description
                    desc = ''
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        if prev_line and not re.match(r'^[\d,]+\.\d{2}$', prev_line) and not re.match(r'^\d+$', prev_line):
                            desc = prev_line
                    
                    line_items.append({
                        'line_num': None,
                        'description': desc,
                        'amount': line
                    })
            
            i += 1
    
    return line_items, lines[max(0, line_item_start-5):min(len(lines), line_item_end+5)]

# Get Non-AP invoices
all_facebook_files = glob.glob(os.path.join(INVOICE_DIR, '246*.pdf')) + \
                    glob.glob(os.path.join(INVOICE_DIR, '247*.pdf'))
non_ap_files = [f for f in all_facebook_files if os.path.basename(f) not in AP_INVOICES]

print(f"Total Non-AP Facebook invoices: {len(non_ap_files)}")
print(f"\n=== Detailed Structure Analysis of Non-AP Invoices ===\n")

# Analyze first 5 invoices in detail
for idx, file_path in enumerate(non_ap_files[:5]):
    file_name = os.path.basename(file_path)
    print(f"\n{'='*80}")
    print(f"Invoice #{idx+1}: {file_name}")
    print(f"{'='*80}")
    
    line_items, context_lines = analyze_invoice_structure(file_path)
    
    print(f"\nFound {len(line_items)} line items")
    
    if line_items:
        print("\nExtracted Line Items:")
        for i, item in enumerate(line_items[:10]):  # Show first 10
            if item['line_num']:
                print(f"  {i+1}. Line #{item['line_num']}")
                print(f"     Description: {item['description'][:100]}")
                print(f"     Amount: {item['amount']}")
            else:
                print(f"  {i+1}. [No line#]")
                print(f"     Description: {item['description'][:100] if item['description'] else 'N/A'}")
                print(f"     Amount: {item['amount']}")
    
    print("\nContext around line items section:")
    for i, line in enumerate(context_lines[:20]):  # Show first 20 lines of context
        print(f"  [{i}] {line[:100]}")

# Look for specific patterns across all Non-AP invoices
print(f"\n\n{'='*80}")
print("PATTERN ANALYSIS ACROSS ALL NON-AP INVOICES")
print(f"{'='*80}")

all_descriptions = []
has_line_numbers = 0
total_line_items = 0

for file_path in non_ap_files:
    line_items, _ = analyze_invoice_structure(file_path)
    total_line_items += len(line_items)
    
    if any(item['line_num'] for item in line_items):
        has_line_numbers += 1
    
    for item in line_items:
        if item['description']:
            all_descriptions.append(item['description'])

print(f"\nStatistics:")
print(f"  Total invoices analyzed: {len(non_ap_files)}")
print(f"  Invoices with line numbers: {has_line_numbers}")
print(f"  Total line items found: {total_line_items}")
print(f"  Average items per invoice: {total_line_items / len(non_ap_files):.1f}")

# Show common description patterns
print(f"\nSample descriptions found:")
unique_descriptions = list(set(all_descriptions))[:20]
for i, desc in enumerate(unique_descriptions):
    print(f"  {i+1}. {desc[:100]}")

# Check specific invoice mentioned in summary
print(f"\n\n{'='*80}")
print("CHECKING SPECIFIC INVOICE: 247036228.pdf")
print(f"{'='*80}")

specific_file = os.path.join(INVOICE_DIR, '247036228.pdf')
if os.path.exists(specific_file):
    line_items, context = analyze_invoice_structure(specific_file)
    print(f"Found {len(line_items)} line items")
    
    if line_items:
        print("\nLine items:")
        for i, item in enumerate(line_items):
            print(f"  {i+1}. Amount: {item['amount']}, Description: {item['description'][:80]}")
    
    print("\nFull context:")
    for i, line in enumerate(context[:30]):
        print(f"  [{i}] {line}")