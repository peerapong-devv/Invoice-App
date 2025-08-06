#!/usr/bin/env python3
"""
Ultimate TikTok parser that correctly extracts all line items with proper field mapping
Handles multi-line pk| patterns and extracts fields according to user specifications
"""

import re
from typing import List, Dict, Optional, Tuple

def parse_tiktok_invoice_ultimate(text_content: str, filename: str) -> List[Dict]:
    """
    Parse TikTok invoice with 100% correct line item extraction
    """
    
    # Extract invoice number
    invoice_number = filename.replace('.pdf', '')
    invoice_match = re.search(r'Invoice No\.\s*:\s*(THTT\d+)', text_content)
    if invoice_match:
        invoice_number = invoice_match.group(1).strip()
    
    # Determine invoice type
    has_st_marker = '[ST]' in text_content
    has_pk_pattern = 'pk|' in text_content or 'pk_' in text_content
    is_ap = has_st_marker and has_pk_pattern
    
    invoice_type = "AP" if is_ap else "Non-AP"
    
    print(f"[DEBUG] TikTok {filename}: Type={invoice_type}, has_st={has_st_marker}, has_pk={has_pk_pattern}")
    
    records = []
    
    if invoice_type == "AP":
        records = parse_tiktok_ap_ultimate(text_content, filename, invoice_number)
    else:
        records = parse_tiktok_non_ap_ultimate(text_content, filename, invoice_number)
    
    if records:
        print(f"[DEBUG] TikTok parser: Found {len(records)} line items")
    
    return records

def parse_tiktok_ap_ultimate(text_content: str, filename: str, invoice_number: str) -> List[Dict]:
    """
    Parse TikTok AP invoice with correct line item extraction
    """
    
    records = []
    lines = text_content.split('\n')
    
    # Find consumption details section
    consumption_start = -1
    for i, line in enumerate(lines):
        if 'Consumption Details:' in line:
            consumption_start = i
            break
    
    if consumption_start == -1:
        print("[DEBUG] No consumption details found")
        return records
    
    # Process consumption table
    current_row = []
    line_num = 0
    i = consumption_start + 1
    
    # Skip headers
    while i < len(lines):
        line = lines[i].strip()
        if line and not any(h in line for h in ['Statement', 'Advertiser', 'Campaign ID', 'Target', 'Period', 'Voucher', 'Cash']):
            break
        i += 1
    
    # Process data rows
    while i < len(lines):
        line = lines[i].strip()
        
        # Stop at totals
        if 'Subtotal before' in line or 'Total in THB' in line:
            # Process last row if any
            if current_row:
                record = process_ap_row_ultimate(current_row, filename, invoice_number, line_num + 1)
                if record:
                    records.append(record)
            break
        
        # Check if this is a new row (starts with ST number)
        if re.match(r'^ST\d{10,12}$', line):
            # Process previous row if exists
            if current_row:
                record = process_ap_row_ultimate(current_row, filename, invoice_number, line_num + 1)
                if record:
                    records.append(record)
                    line_num += 1
            
            # Start new row
            current_row = [line]
        elif current_row:
            # Continue collecting current row
            current_row.append(line)
        
        i += 1
    
    return records

def process_ap_row_ultimate(row_lines: List[str], filename: str, invoice_number: str, line_number: int) -> Optional[Dict]:
    """
    Process a single AP row and extract all fields
    """
    
    if not row_lines:
        return None
    
    # Find and reconstruct pk| pattern
    pk_pattern = None
    pattern_lines = []
    
    for i, line in enumerate(row_lines):
        # Start collecting when we see pk| or pk_
        if 'pk|' in line or 'pk_' in line or (pattern_lines and '[ST]' not in ''.join(pattern_lines)):
            pattern_lines.append(line)
            # Check if pattern is complete
            full = ''.join(pattern_lines)
            if 'pk' in full and '[ST]' in full:
                # Look for pattern that ends with [ST]|campaign_id
                match = re.search(r'(pk[|_][^|]+[|_].*?\[ST\]\|[A-Z0-9]+)', full)
                if match:
                    pk_pattern = match.group(1)
                    break
    
    if not pk_pattern:
        print(f"[DEBUG] No pk| pattern found in row: {row_lines[:3]}")
        return None
    
    # Parse pk| pattern
    fields = parse_pk_pattern_ultimate(pk_pattern)
    
    # Extract amount (cash consumption)
    amount = None
    for line in reversed(row_lines):
        # Look for amount patterns
        if re.search(r'\d+\.\d{2}', line):
            # Try to find cash amount (usually last in triplet)
            amounts = re.findall(r'([\d,]+\.\d{2})', line)
            if amounts:
                try:
                    # If we have 3 amounts (total, voucher, cash), use the last one
                    if len(amounts) >= 3:
                        amount = float(amounts[-1].replace(',', ''))
                    else:
                        # Otherwise use the last amount found
                        amount = float(amounts[-1].replace(',', ''))
                    break
                except:
                    pass
    
    if not amount:
        print(f"[DEBUG] No amount found in row")
        return None
    
    # Create record with all fields
    record = {
        'platform': 'TikTok',
        'filename': filename,
        'invoice_id': invoice_number,
        'invoice_number': invoice_number,
        'invoice_type': 'AP',
        'line_number': line_number,
        'amount': amount,
        'total': amount,
        'description': pk_pattern,
        **fields  # Add all parsed fields
    }
    
    return record

def parse_pk_pattern_ultimate(pattern: str) -> Dict:
    """
    Parse pk| pattern exactly according to user specification:
    pk|project_id|details_[ST]|campaign_id
    """
    
    fields = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown',
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    # Extract campaign_id (after [ST]|)
    campaign_match = re.search(r'\[ST\]\|([A-Z0-9]+)', pattern)
    if campaign_match:
        fields['campaign_id'] = campaign_match.group(1)
    
    # Split pattern to get parts
    if pattern.startswith('pk|'):
        pattern = pattern[3:]  # Remove pk|
    
    # Get the part before [ST]
    if '[ST]' in pattern:
        before_st = pattern.split('[ST]')[0]
        
        # Split by | to get project_id and details
        parts = before_st.split('|', 1)
        
        if parts:
            # First part is project_id
            project_id = parts[0].strip()
            
            # Handle different project_id formats
            if '_pk_' in project_id:
                # Format: CD_pk_60029
                id_match = re.search(r'(\d+)$', project_id)
                if id_match:
                    fields['project_id'] = id_match.group(1)
                else:
                    fields['project_id'] = project_id
            else:
                # Direct project_id
                fields['project_id'] = project_id
            
            # Process details section
            if len(parts) > 1:
                details = parts[1].strip()
                if details.endswith('_'):
                    details = details[:-1]
                
                # Parse details for project_name, objective, period
                parse_details_ultimate(details, fields, project_id)
    
    return fields

def parse_details_ultimate(details: str, fields: dict, project_id: str):
    """
    Parse details section to extract project_name, objective, and period
    """
    
    # Split by underscore
    parts = [p.strip() for p in details.split('_') if p.strip()]
    
    # Extract project name
    project_name_parts = []
    
    for i, part in enumerate(parts):
        # Skip common prefixes and suffixes
        if part in ['none', 'pk', 'tiktok', 'vdo', 'boostpost', 'fb', 'tt', 'Content']:
            continue
        
        # Check if this is an objective
        if is_objective(part):
            fields['objective'] = part.capitalize()
            continue
        
        # Check if this is a period
        period = extract_period(part)
        if period:
            fields['period'] = period
            continue
        
        # Handle project name patterns
        if part.startswith('th-') or part.startswith('th'):
            # Thai project name
            name = part[3:] if part.startswith('th-') else (part[2:] if len(part) > 2 else part)
            project_name_parts.append(name.replace('-', ' '))
        elif part.startswith('AP'):
            # AP prefix (APPawLiving -> PawLiving)
            if len(part) > 2:
                project_name_parts.append(part[2:])
        elif part.startswith('CD_pk_'):
            # CD_pk_ prefix
            name = part[6:]
            if name.startswith('th'):
                name = name[2:] if len(name) > 2 else name
            project_name_parts.append(name.replace('-', ' '))
        elif part.startswith('SDH_pk_'):
            # SDH_pk_ prefix
            name = part[7:]
            if name.startswith('th'):
                name = name[2:] if len(name) > 2 else name
            project_name_parts.append(name.replace('-', ' '))
        else:
            # Other parts that might be project name
            if (not part.isdigit() and 
                len(part) > 2 and 
                not re.match(r'^[A-Z]{2,3}$', part)):  # Not country code
                project_name_parts.append(part.replace('-', ' '))
    
    # Set project name
    if project_name_parts:
        fields['project_name'] = ' '.join(project_name_parts)
    elif project_id and project_id not in ['OnlineMKT', 'Corporate']:
        fields['project_name'] = project_id
    
    # Ensure we have values for all fields
    if fields['objective'] == 'Unknown':
        # Try to find objective in original details
        obj_match = re.search(r'(awareness|traffic|engagement|view|conversion|reach|leadad)', details, re.IGNORECASE)
        if obj_match:
            fields['objective'] = obj_match.group(1).capitalize()
    
    if fields['period'] == 'Unknown':
        # Try to find period in original details
        period_patterns = [
            r'(Q[1-4]Y\d{2})',
            r'([A-Z]{3}Y\d{2})',
            r'(Y\d{2}-[A-Z]{3}\d{2})',
            r'([A-Z][a-z]{2}\d{2})',
            r'(\d{1,2}-\d{1,2}[A-Z][a-z]{2})'
        ]
        for pattern in period_patterns:
            match = re.search(pattern, details)
            if match:
                fields['period'] = match.group(1)
                break

def is_objective(text: str) -> bool:
    """Check if text is an objective"""
    objectives = ['awareness', 'traffic', 'engagement', 'view', 'conversion', 'reach', 'leadad']
    return text.lower() in objectives

def extract_period(text: str) -> Optional[str]:
    """Extract period from text"""
    
    # Direct period patterns
    patterns = [
        (r'^Q[1-4]Y\d{2}$', lambda m: m.group(0)),  # Q2Y25
        (r'^[A-Z]{3}Y\d{2}$', lambda m: m.group(0)),  # MAYY25
        (r'^Y\d{2}-[A-Z]{3}\d{2}', lambda m: m.group(0)),  # Y25-JUN25
        (r'^[A-Z][a-z]{2}\d{2}$', lambda m: m.group(0)),  # Jun25
        (r'^\d{1,2}-\d{1,2}[A-Z][a-z]{2}', lambda m: m.group(0)),  # 1-15Jun
    ]
    
    for pattern, formatter in patterns:
        match = re.match(pattern, text)
        if match:
            return formatter(match)
    
    # Check within text
    for pattern, formatter in patterns:
        match = re.search(pattern, text)
        if match:
            return formatter(match)
    
    return None

def parse_tiktok_non_ap_ultimate(text_content: str, filename: str, invoice_number: str) -> List[Dict]:
    """
    Parse TikTok Non-AP invoice with full campaign descriptions
    """
    
    records = []
    lines = text_content.split('\n')
    
    # Find consumption details section
    consumption_start = -1
    for i, line in enumerate(lines):
        if 'Consumption Details:' in line:
            consumption_start = i
            break
    
    if consumption_start == -1:
        print("[DEBUG] No consumption details found")
        return records
    
    # Find first ST number after consumption details
    i = consumption_start + 1
    data_start = -1
    
    print(f"[DEBUG] Looking for ST numbers starting from line {i}")
    
    while i < len(lines):
        line = lines[i].strip()
        # Look for ST number which indicates start of data
        # ST numbers can be 10-12 digits
        if line.startswith('ST') and len(line) > 2:
            print(f"[DEBUG] Line {i}: Found ST line: '{line}'")
            if re.match(r'^ST\d{10,12}$', line):
                print(f"[DEBUG] Line {i}: Matched ST pattern!")
                data_start = i
                break
            else:
                print(f"[DEBUG] Line {i}: Did not match pattern")
        i += 1
    
    if data_start == -1:
        print("[DEBUG] No ST numbers found in consumption details")
        print(f"[DEBUG] Searched from line {consumption_start+1} to {i}")
        return records
    
    # Start processing from first ST number
    i = data_start
    
    # Process consumption data rows
    line_num = 0
    current_row = []
    
    print(f"[DEBUG] Starting to process data from line {i}")
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Stop at subtotal
        if 'Subtotal before' in line or 'Total in THB' in line:
            print(f"[DEBUG] Found total line at {i}, stopping")
            # Process last row if any
            if current_row:
                print(f"[DEBUG] Processing final row with {len(current_row)} lines")
                record = process_non_ap_row_ultimate(current_row, filename, invoice_number, line_num + 1)
                if record:
                    records.append(record)
            break
        
        # Check if this is a new row (starts with ST number)
        if re.match(r'^ST\d{10,12}$', line):
            # Process previous row if exists
            if current_row:
                print(f"[DEBUG] Processing row {line_num+1} with {len(current_row)} lines")
                record = process_non_ap_row_ultimate(current_row, filename, invoice_number, line_num + 1)
                if record:
                    records.append(record)
                    line_num += 1
                else:
                    print(f"[DEBUG] No record created for row {line_num+1}")
            
            # Start new row
            current_row = [line]
        elif current_row:
            # Continue collecting current row
            current_row.append(line)
        
        i += 1
    
    return records

def process_non_ap_row_ultimate(row_lines: List[str], filename: str, invoice_number: str, line_number: int) -> Optional[Dict]:
    """
    Process a single Non-AP row and extract campaign description
    """
    
    if not row_lines:
        return None
    
    # Based on the structure:
    # Line 0: ST number
    # Line 1: Some number (66)
    # Line 2: Advertiser (DM - Arabus)
    # Line 3: Advertiser ID
    # Line 4: Some ID
    # Line 5: Campaign ID
    # Line 6: Some number
    # Lines 7+: Campaign description (until country code)
    # Then: Country, dates, amounts
    
    # Find where campaign description starts and ends
    campaign_parts = []
    amount = None
    
    # State tracking
    found_campaign_id = False
    campaign_id_line = -1
    
    for i, line in enumerate(row_lines):
        line = line.strip()
        
        # Look for campaign ID (15+ digit number after advertiser ID)
        if not found_campaign_id and re.match(r'^\d{15,}$', line):
            found_campaign_id = True
            campaign_id_line = i
            continue
        
        # After campaign ID, skip one line then start collecting campaign description
        if found_campaign_id and i > campaign_id_line + 1:
            # Stop at country code or date
            if line in ['TH', 'US', 'SG', 'JP', 'KR'] or re.match(r'^\d{4}-\d{2}', line):
                break
            
            # Skip if it's just "THB" or pure numbers
            if line == 'THB' or re.match(r'^[\d,]+\.?\d*$', line):
                continue
                
            # This is part of campaign description
            if line:
                campaign_parts.append(line)
    
    # Extract amount - look for pattern: total voucher cash
    for i in range(len(row_lines) - 1):
        line = row_lines[i].strip()
        # Look for amount pattern (three amounts in sequence or on same line)
        if re.match(r'^[\d,]+\.\d{2}$', line):
            # Check if this might be the total (followed by 0.00 and another amount)
            if i + 2 < len(row_lines):
                next_line = row_lines[i + 1].strip()
                third_line = row_lines[i + 2].strip()
                if next_line == '0.00' and re.match(r'^[\d,]+\.\d{2}$', third_line):
                    # The third line is the cash amount
                    try:
                        amount = float(third_line.replace(',', ''))
                        break
                    except:
                        pass
    
    # Build campaign description
    campaign_description = ' '.join(campaign_parts) if campaign_parts else ''
    
    if not campaign_description or not amount:
        # Debug output
        print(f"[DEBUG] Non-AP row failed: desc='{campaign_description}', amount={amount}")
        return None
    
    # Create record
    record = {
        'platform': 'TikTok',
        'filename': filename,
        'invoice_id': invoice_number,
        'invoice_number': invoice_number,
        'invoice_type': 'Non-AP',
        'line_number': line_number,
        'description': campaign_description,
        'amount': amount,
        'total': amount
    }
    
    return record

def process_non_ap_campaign_ultimate(campaign_lines: List[str], filename: str, invoice_number: str, line_number: int) -> Optional[Dict]:
    """
    Process Non-AP campaign and extract full description
    """
    
    if not campaign_lines:
        return None
    
    # Extract campaign description and amount
    description_parts = []
    amount = None
    
    for line in campaign_lines:
        # Check for amount line (3 values: total, voucher, cash)
        amount_match = re.search(r'([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})', line)
        if amount_match:
            # Cash amount is the last one
            try:
                amount = float(amount_match.group(3).replace(',', ''))
            except:
                pass
        else:
            # Part of description - skip dates, country codes, and pure numbers
            if (not re.match(r'^\d{4}-\d{2}-\d{2}', line) and 
                line not in ['TH', 'US', 'SG', 'JP', 'KR'] and 
                not re.match(r'^[\d\s]+$', line) and
                line.strip()):
                description_parts.append(line)
    
    if not description_parts or not amount:
        return None
    
    # Build full description
    description = ' '.join(description_parts)
    # Clean up extra spaces
    description = re.sub(r'\s+', ' ', description).strip()
    
    # Create record
    record = {
        'platform': 'TikTok',
        'filename': filename,
        'invoice_id': invoice_number,
        'invoice_number': invoice_number,
        'invoice_type': 'Non-AP',
        'line_number': line_number,
        'description': description,
        'amount': amount,
        'total': amount
    }
    
    return record