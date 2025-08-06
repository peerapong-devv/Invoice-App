#!/usr/bin/env python3
"""
Complete Facebook parser fix to achieve 100% accuracy
"""

import re
from typing import Dict, List, Any

def parse_facebook_invoice_complete(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Facebook invoice with complete accuracy"""
    
    # Determine invoice type
    has_st_marker = '[ST]' in text_content
    has_pk_pattern = 'pk|' in text_content
    invoice_type = "AP" if (has_st_marker and has_pk_pattern) else "Non-AP"
    
    # Extract invoice number
    invoice_number = filename.replace('.pdf', '') if filename else 'Unknown'
    invoice_match = re.search(r'Invoice\s+[Nn]umber[:\s]*(\d{9})', text_content)
    if invoice_match:
        invoice_number = invoice_match.group(1)
    
    # Base fields
    base_fields = {
        'platform': 'Facebook',
        'filename': filename,
        'invoice_number': invoice_number,
        'invoice_id': invoice_number
    }
    
    if invoice_type == "AP":
        items = extract_facebook_ap_complete(text_content, base_fields)
    else:
        items = extract_facebook_non_ap_items(text_content, base_fields)
    
    return items

def extract_facebook_ap_complete(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract all Facebook AP items with 100% accuracy"""
    
    items = []
    lines = text_content.split('\n')
    
    # Process line by line
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for lines that start with a line number
        line_match = re.match(r'^(\d+)\s+', line)
        if line_match:
            line_num = int(line_match.group(1))
            
            # Check if this line contains pk| pattern
            if 'pk|' in line and '[ST]' in line:
                # Build the complete text for this item
                item_text = line
                j = i + 1
                
                # Look for the amount in subsequent lines
                # The amount might be on the same line, next line, or a few lines down
                found_amount = False
                amount_str = ''
                
                # First check if amount is on the same line
                same_line_amount = re.search(r'([\d,]+\.\d{2})\s*$', line)
                if same_line_amount:
                    amount_str = same_line_amount.group(1)
                    found_amount = True
                else:
                    # Look in next few lines for the amount
                    while j < len(lines) and j < i + 5:  # Check up to 5 lines ahead
                        next_line = lines[j].strip()
                        
                        # Skip empty lines
                        if not next_line:
                            j += 1
                            continue
                        
                        # If we hit a new line number, stop
                        if re.match(r'^\d+\s+', next_line):
                            break
                        
                        # Check if this line is just an amount
                        amount_only = re.match(r'^([\d,]+\.\d{2})\s*$', next_line)
                        if amount_only:
                            amount_str = amount_only.group(1)
                            found_amount = True
                            break
                        
                        # Skip lines that are annotations (like "- Coupons:")
                        if next_line.startswith('-'):
                            j += 1
                            continue
                        
                        # Check if amount is at the end of this line
                        end_amount = re.search(r'([\d,]+\.\d{2})\s*$', next_line)
                        if end_amount:
                            amount_str = end_amount.group(1)
                            found_amount = True
                            break
                        
                        # Otherwise, append to item text
                        item_text += ' ' + next_line
                        j += 1
                
                if found_amount and amount_str:
                    # Extract the pk pattern
                    pk_match = re.search(r'(pk\|[^\[]+\[ST\]\|[A-Z0-9]+)', item_text)
                    if pk_match:
                        pk_pattern = pk_match.group(1)
                        
                        try:
                            amount = float(amount_str.replace(',', ''))
                            # Skip negative amounts (credits)
                            if amount < 0:
                                i += 1
                                continue
                                
                            ap_fields = parse_facebook_ap_pattern_complete(pk_pattern)
                            
                            item = {
                                **base_fields,
                                'invoice_type': 'AP',
                                'line_number': line_num,
                                'amount': amount,
                                'total': amount,
                                'description': pk_pattern,
                                **ap_fields
                            }
                            items.append(item)
                        except:
                            pass
        
        i += 1
    
    # Additional pass: Find any patterns we might have missed
    # This handles cases where the format might be different
    text_no_newlines = ' '.join(lines)
    
    # Pattern: pk|...[ST]|id followed by amount (with possible text in between)
    pattern = r'(pk\|[^\[]+\[ST\]\|[A-Z0-9]+)[^\d]*?([\d,]+\.\d{2})'
    
    # Track what we've already found
    found_line_numbers = {item['line_number'] for item in items}
    
    # Also look for line numbers in the text to avoid duplicates
    for match in re.finditer(pattern, text_no_newlines):
        pk_str = match.group(1)
        amount_str = match.group(2)
        
        # Check if there's a line number before this pattern
        before_text = text_no_newlines[:match.start()]
        line_num_match = re.search(r'(\d{1,3})\s+[^\d]*$', before_text)
        
        if line_num_match:
            line_num = int(line_num_match.group(1))
            if line_num not in found_line_numbers:
                try:
                    amount = float(amount_str.replace(',', ''))
                    if amount > 0:  # Skip negative amounts
                        ap_fields = parse_facebook_ap_pattern_complete(pk_str)
                        
                        item = {
                            **base_fields,
                            'invoice_type': 'AP',
                            'line_number': line_num,
                            'amount': amount,
                            'total': amount,
                            'description': pk_str,
                            **ap_fields
                        }
                        items.append(item)
                        found_line_numbers.add(line_num)
                except:
                    pass
    
    # Sort by line number
    return sorted(items, key=lambda x: x.get('line_number', 999))

def clean_facebook_text(text: str) -> str:
    """Remove headers/footers to help with split patterns"""
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip common header/footer patterns
        if any(skip in line for skip in [
            'Meta Platforms Ireland Limited',
            'Merrion Road',
            'Dublin 4',
            'VAT ID:',
            'INVOICE',
            'Page:',
            'BILL TO:',
            'ATTN:',
            'Advertiser:',
            'PO Number:',
            'Line#',
            'Description - Advertising Services',
            'Campaign Label',
            'Total',
            'INVOICE NUMBER MUST BE REFERENCED',
            'The customer shall account for VAT',
            'Remit Payment To:',
            'Bank Details:',
            'www.facebook.com',
            'ar@meta.com',
            'Subtotal:',
            'Freight:',
            'VAT @0%:',
            'Invoice Total:',
            'Invoice Currency:',
            'Payment Terms:',
            'Account Id / Group:',
            'Billing Period:'
        ]):
            continue
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def parse_facebook_ap_pattern_complete(pattern: str) -> Dict[str, str]:
    """Parse all Facebook AP pattern variations"""
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown', 
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    # Clean pattern - remove newlines and extra spaces
    pattern = re.sub(r'\s+', ' ', pattern.replace('\n', ' ').strip())
    
    # Extract campaign_id (after [ST]|)
    if '[ST]|' in pattern:
        parts = pattern.split('[ST]|')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            # Clean campaign ID - remove any trailing text
            campaign_id = re.match(r'^([A-Z0-9]+)', campaign_id)
            if campaign_id:
                result['campaign_id'] = campaign_id.group(1)
        pattern = parts[0]  # Work with part before [ST]
    
    # Split by pipes
    parts = pattern.split('|')
    
    if len(parts) >= 2:
        # Second part analysis
        second_part = parts[1] if len(parts) > 1 else ''
        third_part = parts[2] if len(parts) > 2 else ''
        
        # Extract project ID from various patterns
        
        # Pattern 1: Direct numeric ID (e.g., "40093")
        if re.match(r'^\d+$', second_part):
            result['project_id'] = second_part
            details = third_part
        
        # Pattern 2: SDH_pk_40093_... (ID after _pk_)
        elif '_pk_' in second_part:
            id_match = re.search(r'_pk_(\d+)', second_part)
            if id_match:
                result['project_id'] = id_match.group(1)
            details = second_part + (('|' + third_part) if third_part else '')
        
        # Pattern 3: TH_pk_40084-BANGYAI-...
        elif re.match(r'^(TH|SDH|CD)_pk_', second_part):
            id_match = re.search(r'pk_(\d+)', second_part)
            if id_match:
                result['project_id'] = id_match.group(1)
            # Extract project name from pattern
            if '-BANGYAI-' in second_part:
                result['project_name'] = 'BANGYAI District'
            elif 'APTOWNHOME' in second_part:
                result['project_name'] = 'AP Townhome'
            details = second_part + (('|' + third_part) if third_part else '')
        
        # Pattern 4: Corporate_pk_Corporate
        elif 'Corporate' in second_part:
            result['project_id'] = 'Corporate'
            result['project_name'] = 'Corporate'
            details = second_part + (('|' + third_part) if third_part else '')
        
        # Pattern 5: OnlineMKT
        elif 'OnlineMKT' in second_part:
            result['project_id'] = 'OnlineMKT'
            result['project_name'] = 'Online Marketing'
            details = second_part + (('|' + third_part) if third_part else '')
        
        # Pattern 6: Just SDH/TH/CD
        elif second_part in ['SDH', 'TH', 'CD']:
            result['project_id'] = second_part
            result['project_name'] = {
                'SDH': 'Single Detached House',
                'TH': 'Townhome', 
                'CD': 'Condominium'
            }.get(second_part, second_part)
            details = third_part
        
        # Pattern 7: SDH|SDH_pk_none_none...
        elif second_part == 'SDH' and third_part.startswith('SDH_pk_'):
            result['project_id'] = 'SDH'
            result['project_name'] = 'Single Detached House'
            details = third_part
        
        else:
            # Unknown pattern, use second part as details
            details = second_part + (('|' + third_part) if third_part else '')
        
        # Parse details for additional fields
        if 'details' in locals():
            parse_details_complete(details, result)
    
    return result

def parse_details_complete(details: str, result: dict):
    """Parse details section comprehensively"""
    
    # Clean details
    details = details.replace('\n', ' ').strip()
    
    # Extract project name if not set
    if result['project_name'] == 'Unknown':
        # Various project name patterns
        project_patterns = [
            (r'single-detached-house', 'Single Detached House'),
            (r'townhome', 'Townhome'),
            (r'town', 'Townhome'),
            (r'condominium', 'Condominium'),
            (r'upcountry-projects-apitown', 'Apitown'),
            (r'the-city-', 'The City'),
            (r'centro-', 'Centro'),
            (r'moden-', 'Moden'),
            (r'the-palazzo', 'The Palazzo'),
            (r'PlenoTown', 'Pleno Town')
        ]
        
        for pattern, name in project_patterns:
            if pattern in details.lower():
                result['project_name'] = name
                break
        
        # Extract specific project names
        if 'AP-' in details:
            name_match = re.search(r'AP-([^_]+)', details)
            if name_match:
                result['project_name'] = 'AP-' + name_match.group(1)
    
    # Extract objective
    objectives = ['Awareness', 'Conversion', 'LeadAd', 'Traffic', 'Engagement', 'View', 'VDO-View']
    for obj in objectives:
        if obj in details:
            result['objective'] = obj.replace('VDO-View', 'View')
            break
    
    # Extract period with comprehensive patterns
    period_patterns = [
        (r'(Q[1-4]Y\d{2})', None),           # Q2Y25
        (r'Y\d{2}-([A-Z]{3}\d{2})', 1),     # Y25-JUN25
        (r'([A-Z]{3}\d{2})', None),          # JUN25
        (r'([A-Z][a-z]{2}\d{2})', None),     # Jun25
        (r'-([A-Z][a-z]{2})-', 1),           # -Jun-
        (r'Y25-([A-Z]{3})-', 1),             # Y25-JUN-
        (r'Q2Y25-([A-Z]{3})', 1),            # Q2Y25-JUN
        (r'([A-Z]{3})-', None),              # JUN-
    ]
    
    for pattern, group in period_patterns:
        period_match = re.search(pattern, details)
        if period_match:
            if group is not None:
                result['period'] = period_match.group(group)
            else:
                result['period'] = period_match.group(0)
            break

def extract_facebook_non_ap_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Facebook Non-AP items (working implementation)"""
    
    items = []
    lines = text_content.split('\n')
    
    # Find ar@meta.com marker
    start_idx = -1
    for i, line in enumerate(lines):
        if 'ar@meta.com' in line:
            start_idx = i
            break
    
    if start_idx == -1:
        return []
    
    # Extract line items after marker
    i = start_idx + 1
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if it's a line number
        if line.isdigit():
            line_num = int(line)
            
            # Collect description (next 1-3 lines)
            description_parts = []
            j = i + 1
            
            while j < len(lines) and j < i + 10:
                next_line = lines[j].strip()
                
                # Stop if we hit amount or next line number
                if re.match(r'^[\d,]+\.\d{2}\s*$', next_line):
                    # Found amount
                    try:
                        amount = float(next_line.replace(',', ''))
                        
                        item = {
                            **base_fields,
                            'invoice_type': 'Non-AP',
                            'line_number': line_num,
                            'description': ' '.join(description_parts),
                            'amount': amount,
                            'total': amount
                        }
                        items.append(item)
                        i = j
                        break
                    except:
                        pass
                elif next_line.isdigit():
                    # Hit next line number
                    i = j - 1
                    break
                elif next_line:
                    # Part of description
                    description_parts.append(next_line)
                
                j += 1
            
            if j >= len(lines) or j >= i + 10:
                i = j
        
        i += 1
    
    return items

if __name__ == "__main__":
    # Test with problematic invoices
    import fitz
    
    test_files = {
        "246543739.pdf": 1985559.44,
        "246546622.pdf": 973675.24,
        "246578231.pdf": 94498.17,
        "246649305.pdf": 28316.47,
        "246727587.pdf": 1066985.58,
        "246738919.pdf": 788488.72,
        "246774670.pdf": 553692.93,
        "246791975.pdf": 1417663.24,
        "246865374.pdf": 506369.23,
        "246952437.pdf": 163374.47
    }
    
    for filename, expected_total in list(test_files.items())[:3]:  # Test first 3
        filepath = f"../Invoice for testing/{filename}"
        try:
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            items = parse_facebook_invoice_complete(text, filename)
            total = sum(item['amount'] for item in items)
            accuracy = (total / expected_total * 100) if expected_total > 0 else 0
            
            print(f"\n{filename}:")
            print(f"  Expected: {expected_total:,.2f}")
            print(f"  Extracted: {total:,.2f}")
            print(f"  Accuracy: {accuracy:.2f}%")
            print(f"  Items: {len(items)}")
            
            # Show what we're missing
            if accuracy < 99:
                diff = expected_total - total
                print(f"  Missing: {diff:,.2f} THB")
                
                # Check invoice structure
                print(f"\n  Checking invoice structure...")
                all_amounts = re.findall(r'([\d,]+\.\d{2})', text)
                amounts_sum = sum(float(a.replace(',', '')) for a in all_amounts if float(a.replace(',', '')) < 100000)
                print(f"  Sum of all amounts < 100k: {amounts_sum:,.2f}")
                
                # Count all pk| patterns
                pk_count = len(re.findall(r'pk\|', text))
                print(f"  Total pk| patterns in invoice: {pk_count}")
                print(f"  We extracted: {len(items)}")
                
        except Exception as e:
            print(f"\n{filename}: ERROR - {str(e)}")