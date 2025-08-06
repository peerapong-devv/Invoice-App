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

def extract_nonap_line_items(file_path):
    """Extract line items from Facebook Non-AP invoices"""
    with fitz.open(file_path) as doc:
        full_text = "\n".join(page.get_text() for page in doc)
    
    lines = full_text.split('\n')
    
    # Find the line items section - it comes after the payment details
    # Look for lines starting with digits followed by campaign descriptions
    line_items = []
    
    # Start looking after the bank details section
    start_looking = False
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Once we see "ar@meta.com", the line items start
        if "ar@meta.com" in line:
            start_looking = True
            continue
            
        if start_looking and line:
            # Look for line number pattern (digit at start of line)
            if re.match(r'^(\d+)$', line):
                line_num = line
                
                # Look for description in next lines
                desc_lines = []
                amount = None
                
                j = i + 1
                while j < len(lines) and j < i + 10:
                    next_line = lines[j].strip()
                    
                    if not next_line:  # Skip empty lines
                        j += 1
                        continue
                    
                    # Check if it's an amount (ends with space)
                    amount_match = re.match(r'^([\d,]+\.\d{2})\s*$', next_line)
                    if amount_match:
                        amount = amount_match.group(1)
                        break
                    
                    # Check if it's another line number (stop here)
                    if re.match(r'^\d+$', next_line):
                        break
                    
                    # Otherwise, it's part of the description
                    desc_lines.append(next_line)
                    j += 1
                
                if amount:
                    description = ' '.join(desc_lines) if desc_lines else ''
                    line_items.append({
                        'line_num': line_num,
                        'description': description,
                        'amount': amount
                    })
    
    return line_items

def get_invoice_total(file_path):
    """Extract the invoice total"""
    with fitz.open(file_path) as doc:
        full_text = "\n".join(page.get_text() for page in doc)
    
    lines = full_text.split('\n')
    
    for i, line in enumerate(lines):
        if 'Invoice Total:' in line and i + 1 < len(lines):
            return lines[i + 1].strip()
    
    return None

# Get Non-AP invoices
all_facebook_files = glob.glob(os.path.join(INVOICE_DIR, '246*.pdf')) + \
                    glob.glob(os.path.join(INVOICE_DIR, '247*.pdf'))
non_ap_files = [f for f in all_facebook_files if os.path.basename(f) not in AP_INVOICES]

print(f"Total Non-AP Facebook invoices: {len(non_ap_files)}")
print(f"\n{'='*100}")
print("FACEBOOK NON-AP INVOICE STRUCTURE ANALYSIS")
print(f"{'='*100}")

# Analyze structure patterns
total_items = 0
total_invoices_with_items = 0
all_descriptions = []
amount_patterns = set()

# Analyze first 10 invoices in detail
print(f"\nDETAILED ANALYSIS (First 10 invoices):")
for idx, file_path in enumerate(non_ap_files[:10]):
    file_name = os.path.basename(file_path)
    line_items = extract_nonap_line_items(file_path)
    invoice_total = get_invoice_total(file_path)
    
    print(f"\n{idx+1:2d}. {file_name}")
    print(f"    Line Items: {len(line_items)}")
    print(f"    Invoice Total: {invoice_total}")
    
    if line_items:
        total_invoices_with_items += 1
        total_items += len(line_items)
        
        # Calculate sum of line items
        line_sum = 0
        for item in line_items:
            try:
                amount = float(item['amount'].replace(',', ''))
                line_sum += amount
            except:
                pass
        
        print(f"    Line Items Sum: {line_sum:,.2f}")
        
        print(f"    Sample Items:")
        for i, item in enumerate(line_items[:3]):
            desc_short = item['description'][:60] + "..." if len(item['description']) > 60 else item['description']
            print(f"      Line {item['line_num']}: {desc_short} -> {item['amount']}")
            
            # Collect patterns
            all_descriptions.append(item['description'])
            amount_patterns.add(item['amount'])

# Analyze all invoices for statistics
print(f"\n{'='*100}")
print("COMPREHENSIVE STATISTICS:")
print(f"{'='*100}")

all_items = 0
all_invoices_with_items = 0

for file_path in non_ap_files:
    line_items = extract_nonap_line_items(file_path)
    if line_items:
        all_invoices_with_items += 1
        all_items += len(line_items)

print(f"Total Non-AP invoices: {len(non_ap_files)}")
print(f"Invoices with line items: {all_invoices_with_items}")
print(f"Invoices without line items: {len(non_ap_files) - all_invoices_with_items}")
print(f"Total line items found: {all_items}")
print(f"Average items per invoice: {all_items / len(non_ap_files):.1f}")
print(f"Average items per invoice (with items): {all_items / max(1, all_invoices_with_items):.1f}")

# Analyze description patterns
print(f"\nDESCRIPTION PATTERNS:")
unique_descriptions = list(set(all_descriptions))
print(f"Unique descriptions found: {len(unique_descriptions)}")

# Group by common patterns
campaign_patterns = {}
for desc in unique_descriptions:
    # Extract campaign type patterns
    if '|' in desc:
        parts = desc.split('|')
        if len(parts) >= 2:
            campaign_key = parts[0].strip()
            if campaign_key not in campaign_patterns:
                campaign_patterns[campaign_key] = 0
            campaign_patterns[campaign_key] += 1

print(f"\nCampaign Pattern Analysis:")
sorted_patterns = sorted(campaign_patterns.items(), key=lambda x: x[1], reverse=True)
for pattern, count in sorted_patterns[:10]:
    print(f"  {pattern}: {count} occurrences")

# Analyze structure format
print(f"\nSTRUCTURE FORMAT ANALYSIS:")
print("Non-AP Facebook invoices follow this structure:")
print("1. Standard invoice header with Meta Platforms Ireland Limited")
print("2. Bill To information")
print("3. Invoice details (number, date, period)")
print("4. Payment instructions and bank details")
print("5. Subtotal, VAT, Total summary")
print("6. Line items section (AFTER payment details):")
print("   - Line number (single digit on its own line)")
print("   - Campaign description (one or more lines)")
print("   - Amount (on its own line)")

print(f"\nKEY DIFFERENCES FROM AP INVOICES:")
print("1. NO [ST] markers anywhere in the invoice")
print("2. Simple campaign descriptions (not structured pk| format)")
print("3. Line items appear at the END of invoice (not in main body)")
print("4. Campaign descriptions are human-readable, not coded")
print("5. Amount format: XXX,XXX.XX (with trailing space)")

# Show sample extraction
print(f"\n{'='*100}")
print("SAMPLE EXTRACTION FROM 247036228.pdf:")
print(f"{'='*100}")

sample_file = os.path.join(INVOICE_DIR, '247036228.pdf')
if os.path.exists(sample_file):
    sample_items = extract_nonap_line_items(sample_file)
    sample_total = get_invoice_total(sample_file)
    
    print(f"Invoice Total: {sample_total}")
    print(f"Line Items ({len(sample_items)}):")
    
    for item in sample_items:
        print(f"  Line {item['line_num']}: {item['description']}")
        print(f"                  Amount: {item['amount']}")
    
    # Verify sum
    sum_check = sum(float(item['amount'].replace(',', '')) for item in sample_items)
    print(f"\nVerification:")
    print(f"  Sum of line items: {sum_check:,.2f}")
    print(f"  Invoice total: {sample_total}")
    print(f"  Match: {abs(sum_check - float(sample_total.replace(',', ''))) < 0.01}")