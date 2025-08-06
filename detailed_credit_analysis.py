import fitz
import re
import sys
import io
import os

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def detailed_credit_analysis(filename):
    """Detailed analysis of credit note structure"""
    print(f"\n{'='*80}")
    print(f"DETAILED CREDIT NOTE ANALYSIS: {filename}")
    print('='*80)
    
    filepath = os.path.join("Invoice for testing", filename)
    
    with fitz.open(filepath) as doc:
        full_text = "\n".join(page.get_text() for page in doc)
    
    lines = full_text.split('\n')
    
    # Show raw text around invalid activities
    print("\n1. FULL TEXT ANALYSIS AROUND INVALID ACTIVITIES:")
    print("-" * 60)
    
    for i, line in enumerate(lines):
        if "กิจกรรมที่ไม่ถูกต้อง" in line:
            print(f"\nInvalid activity found at line {i}:")
            # Show more context
            start = max(0, i-5)
            end = min(len(lines), i+10)
            for j in range(start, end):
                marker = ">>> " if j == i else "    "
                print(f"{marker}{j:3d}: {lines[j]}")
    
    print("\n2. AMOUNT PATTERN ANALYSIS:")
    print("-" * 60)
    
    # Find all amounts and their positions
    amounts = []
    for i, line in enumerate(lines):
        line = line.strip()
        # Look for Thai amounts with - sign
        if re.match(r'^-\d+[\d,]*\.\d{2}$', line):
            amounts.append((i, line, 'negative'))
        elif re.match(r'^\d+[\d,]*\.\d{2}$', line):
            amounts.append((i, line, 'positive'))
    
    print(f"Found {len(amounts)} amounts:")
    for line_num, amount, type_amt in amounts:
        print(f"  Line {line_num:3d}: {amount:>12} ({type_amt})")
        
        # Look for descriptions in nearby lines
        for j in range(max(0, line_num-3), min(len(lines), line_num+8)):
            if "กิจกรรมที่ไม่ถูกต้อง" in lines[j]:
                print(f"    -> Related invalid activity at line {j}")
                break
    
    print("\n3. EXTRACTING INVALID ACTIVITY DETAILS:")
    print("-" * 60)
    
    # Extract all invalid activity entries with their amounts
    invalid_entries = []
    
    for i, line in enumerate(lines):
        if "กิจกรรมที่ไม่ถูกต้อง" in line:
            # Look backwards for the amount
            amount = None
            for j in range(i-1, max(0, i-10), -1):
                line_check = lines[j].strip()
                if re.match(r'^-\d+[\d,]*\.\d{2}$', line_check):
                    amount = line_check
                    break
            
            # Get the full description (might span multiple lines)
            desc_lines = [line]
            k = i + 1
            while k < len(lines) and k < i + 10:
                next_line = lines[k].strip()
                # Stop if we hit another amount or structure
                if re.match(r'^-?\d+[\d,]*\.\d{2}$', next_line):
                    break
                if next_line and not any(keyword in next_line for keyword in ['ยอดรวม', 'GST', 'หมายเลข']):
                    desc_lines.append(next_line)
                k += 1
            
            full_description = ' '.join(desc_lines)
            
            invalid_entries.append({
                'amount': amount,
                'description': full_description,
                'line_number': i
            })
    
    print(f"Found {len(invalid_entries)} invalid activity entries:")
    
    for i, entry in enumerate(invalid_entries):
        print(f"\n{i+1}. Amount: {entry['amount']}")
        print(f"   Line: {entry['line_number']}")
        print(f"   Description: {entry['description'][:150]}...")
        
        # Extract specific details
        desc = entry['description']
        
        # Original invoice number
        invoice_match = re.search(r'หมายเลขใบแจ้งหนี้เดิม:\s*(\d+)', desc)
        if invoice_match:
            print(f"   -> Original Invoice: {invoice_match.group(1)}")
        
        # Service month
        month_match = re.search(r'เดือนที่ใช้บริการ:\s*([^,]+)', desc)
        if month_match:
            print(f"   -> Service Month: {month_match.group(1).strip()}")
        
        # Budget account
        budget_match = re.search(r'ชื่องบประมาณบัญชี:\s*([^,]+)', desc)
        if budget_match:
            print(f"   -> Budget Account: {budget_match.group(1).strip()}")
        
        # Campaign name
        campaign_match = re.search(r'ชื่อแคมเปญ:\s*(.+)', desc)
        if campaign_match:
            campaign = campaign_match.group(1).strip()
            # Clean up campaign name
            campaign = re.sub(r'\s+', ' ', campaign)
            if len(campaign) > 100:
                campaign = campaign[:100] + "..."
            print(f"   -> Campaign: {campaign}")
    
    print("\n4. CREDIT NOTE SUMMARY:")
    print("-" * 60)
    
    # Calculate total credit amount
    total_credit = 0
    valid_amounts = []
    
    for entry in invalid_entries:
        if entry['amount']:
            try:
                amount_val = float(entry['amount'].replace(',', ''))
                valid_amounts.append(amount_val)
                total_credit += amount_val
            except:
                pass
    
    print(f"Total invalid activity entries: {len(invalid_entries)}")
    print(f"Valid amounts found: {len(valid_amounts)}")
    print(f"Individual amounts: {valid_amounts}")
    print(f"Sum of individual amounts: {total_credit}")
    
    # Check against invoice total
    total_match = re.search(r'ยอดรวมในสกุลเงิน THB\s*(-?\d+[\d,]*\.\d{2})', full_text)
    if total_match:
        invoice_total = float(total_match.group(1).replace(',', ''))
        print(f"Invoice total from footer: {invoice_total}")
        print(f"Difference: {abs(total_credit - invoice_total)}")

# Test all credit notes
credit_notes = [
    "5297692790.pdf",
    "5297785878.pdf", 
    "5298281913.pdf",
    "5298615229.pdf",
    "5300482566.pdf"
]

for cn in credit_notes[:2]:  # Test first 2
    detailed_credit_analysis(cn)
    print("\n" + "="*80)
    input("Press Enter to continue to next file...")