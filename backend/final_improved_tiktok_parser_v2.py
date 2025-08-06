#!/usr/bin/env python3

import re
from collections import Counter

def parse_tiktok_invoice_detailed(text_content: str, filename: str):
    """
    Final improved TikTok parser v2 with better AP pattern parsing
    
    For AP invoices: Extract agency, project_id, project_name, objective, period, campaign_id from campaign name
    For Non-AP invoices: Extract full campaign name as description
    """
    
    lines = text_content.split('\n')
    
    # Base fields
    base_fields = {
        'platform': 'TikTok',
        'filename': filename
    }
    
    # Extract basic invoice information
    invoice_info = extract_tiktok_invoice_info(lines)
    base_fields.update(invoice_info)
    
    # Determine invoice type
    invoice_type = determine_tiktok_invoice_type_enhanced(text_content)
    
    print(f"[DEBUG] TikTok {filename}: Type={invoice_type}")
    
    # Check if this has consumption details
    if 'Consumption Details:' in text_content:
        # Extract detailed line items from consumption table
        line_items = extract_tiktok_consumption_details(text_content, base_fields, invoice_type)
        
        if line_items:
            print(f"[DEBUG] TikTok detailed parser: Found {len(line_items)} line items")
            return line_items
    
    # Fallback: single invoice total record
    invoice_total = find_tiktok_invoice_total(lines, filename)
    
    if invoice_total > 0:
        record = {
            **base_fields,
            'invoice_type': invoice_type,
            'description': f"TikTok {invoice_type} Invoice Total",
            'amount': invoice_total
        }
        print(f"[DEBUG] TikTok fallback: Invoice total {invoice_total:,.2f} THB")
        return [record]
    
    return []

def extract_tiktok_consumption_details(text_content: str, base_fields: dict, invoice_type: str):
    """
    Extract detailed line items from TikTok Consumption Details table
    """
    
    lines = text_content.split('\n')
    records = []
    
    # Find consumption details section
    consumption_section = extract_consumption_section(lines)
    
    if not consumption_section:
        print("[DEBUG] No consumption section found")
        return []
    
    # Parse table data
    table_data = parse_tiktok_consumption_table_improved(consumption_section)
    
    # Convert to records
    for row_data in table_data:
        if invoice_type == "AP":
            record = create_tiktok_ap_record(row_data, base_fields)
        else:
            record = create_tiktok_non_ap_record(row_data, base_fields)
        
        if record:
            records.append(record)
    
    return records

def extract_consumption_section(lines):
    """Extract the consumption details section from lines"""
    
    consumption_lines = []
    in_section = False
    
    for line in lines:
        line_clean = line.strip()
        
        if 'Consumption Details:' in line_clean:
            in_section = True
            continue
        
        if in_section:
            # Stop at summary sections
            if any(stop_word in line_clean.lower() for stop_word in ['total in thb', 'please note that', 'subtotal before margin']):
                break
            
            if line_clean:
                consumption_lines.append(line_clean)
    
    return consumption_lines

def parse_tiktok_consumption_table_improved(consumption_lines):
    """
    Improved parsing of TikTok consumption table data
    Handles pk| patterns split across lines
    """
    
    table_rows = []
    current_row_lines = []
    
    # Skip header lines
    header_keywords = ['Statement', 'Advertiser', 'Campaign ID', 'Campaign Name', 'Target', 'Country', 'Period', 'Total Consumption', 'Voucher', 'Cash']
    
    i = 0
    while i < len(consumption_lines):
        line = consumption_lines[i].strip()
        
        # Skip obvious header lines
        if any(header in line for header in header_keywords):
            i += 1
            continue
        
        # Start of new row - multiple patterns
        # Pattern 1: ST followed by numbers
        # Pattern 2: Number+Letter pattern like "59ZP - Prakit"
        # Pattern 3: Just "AP - " at start
        # Pattern 4: Number+pk| pattern like "7pk|"
        if (re.match(r'^ST\d+', line) or 
            re.match(r'^\d{2}[A-Z]+\s*-\s*', line) or
            re.match(r'^\d+AP\s*-\s*', line) or
            re.search(r'\d+pk\|', line)):
            
            # Process previous row if exists
            if current_row_lines:
                row_data = process_tiktok_table_row_improved(current_row_lines)
                if row_data:
                    table_rows.append(row_data)
            
            # Start new row
            current_row_lines = [line]
            i += 1
            continue
        
        # Continue building current row
        if current_row_lines:
            current_row_lines.append(line)
            
            # Check if this line ends the row (contains final amounts)
            if re.search(r'\d{1,3}(?:,\d{3})*\.\d{2}\s*0\.00\s*\d{1,3}(?:,\d{3})*\.\d{2}', line):
                # End of row
                row_data = process_tiktok_table_row_improved(current_row_lines)
                if row_data:
                    table_rows.append(row_data)
                current_row_lines = []
        
        i += 1
    
    # Process final row if any
    if current_row_lines:
        row_data = process_tiktok_table_row_improved(current_row_lines)
        if row_data:
            table_rows.append(row_data)
    
    return table_rows

def process_tiktok_table_row_improved(row_lines):
    """
    Improved processing of table rows
    Handles pk| patterns that may be split across lines
    """
    
    if not row_lines:
        return None
    
    # Join all lines for easier extraction
    full_text = ' '.join(row_lines)
    
    row_data = {}
    
    # Extract Statement ID
    statement_match = re.search(r'ST(\d+)', full_text)
    row_data['statement_id'] = statement_match.group(1) if statement_match else 'Unknown'
    
    # Extract Advertiser (agency) - handle both AP and Non-AP patterns
    advertiser_match = re.search(r'(\d*[A-Z]+\s*-\s*[^0-9]+?)(?=\s*\d{10,}|$)', full_text)
    row_data['agency'] = advertiser_match.group(1).strip() if advertiser_match else 'Unknown'
    
    # Extract Advertiser ID
    advertiser_id_match = re.search(r'(\d{10,15})', full_text)
    row_data['advertiser_id'] = advertiser_id_match.group(1) if advertiser_id_match else 'Unknown'
    
    # Extract Campaign ID (longer number)
    campaign_id_match = re.search(r'(\d{15,})', full_text)
    row_data['campaign_id'] = campaign_id_match.group(1) if campaign_id_match else 'Unknown'
    
    # Extract Campaign Name - reconstructing from lines
    campaign_name = extract_campaign_name_improved_v2(row_lines)
    row_data['campaign_name'] = campaign_name
    
    # Extract Target Country
    country_match = re.search(r'\s(TH|US|SG|JP|KR)\s', full_text)
    row_data['target_country'] = country_match.group(1) if country_match else 'TH'
    
    # Extract Period
    period_match = re.search(r'(\d{4}-\d{2}-\d{2}\s*~\s*\d{4}-\d{2}-\d{2})', full_text)
    row_data['period'] = period_match.group(1) if period_match else 'Unknown'
    
    # Extract amounts
    amount = extract_amount_from_row(full_text)
    row_data['amount'] = amount
    
    return row_data if row_data['amount'] > 0 else None

def extract_campaign_name_improved_v2(row_lines):
    """
    Improved campaign name extraction v2
    Better handling of pk| patterns split across multiple lines
    """
    
    # Check if this is an AP invoice (has pk| pattern)
    full_text = ' '.join(row_lines)
    
    if 'pk|' in full_text:
        # Find where pk| starts and reconstruct the full pattern
        campaign_parts = []
        collecting = False
        pk_found_idx = -1
        
        for i, line in enumerate(row_lines):
            # Look for pk| pattern (may have number prefix)
            if 'pk|' in line:
                pk_found_idx = i
                # Extract from pk| onwards, removing any number prefix
                pk_start = line.find('pk|')
                # Get everything before pk| to check if there's a number
                before_pk = line[:pk_start]
                if before_pk and before_pk[-1].isdigit():
                    # Remove the digit prefix
                    campaign_parts.append(line[pk_start:])
                else:
                    campaign_parts.append(line[pk_start:])
                collecting = True
            elif collecting and i == pk_found_idx + 1:
                # Next line after pk| - check if it's continuation
                line_clean = line.strip()
                # Stop conditions
                if re.match(r'^(TH|US|SG|JP|KR)', line_clean):
                    break
                if re.match(r'^\d{4}-\d{2}', line_clean):
                    break
                if re.match(r'^\d{10,}$', line_clean):  # Skip ID lines
                    continue
                # This is part of the campaign name
                campaign_parts.append(line_clean)
            elif collecting:
                line_clean = line.strip()
                # Check for end markers
                if '[ST]|' in line_clean:
                    # Add this line and stop
                    campaign_parts.append(line_clean)
                    break
                elif re.match(r'^(TH|US|SG|JP|KR)', line_clean) or re.match(r'^\d{4}-\d{2}', line_clean):
                    break
                elif line_clean and not re.match(r'^\d+$', line_clean):
                    campaign_parts.append(line_clean)
        
        if campaign_parts:
            # Join and clean the campaign name
            full_campaign = ''.join(campaign_parts)
            # Clean up - remove trailing date/country/amount info
            # Look for pattern ending with [ST]|campaign_id
            st_pattern = re.search(r'(pk\|.+?\[ST\]\|[A-Z0-9]+)', full_campaign)
            if st_pattern:
                return st_pattern.group(1)
            else:
                # Fallback - remove trailing data
                full_campaign = re.sub(r'(TH|US|SG|JP|KR)\s*\d{4}-\d{2}.*$', '', full_campaign)
                return full_campaign.strip()
    
    # For Non-AP invoices, extract descriptive campaign name
    # Find where campaign name starts (after IDs)
    start_idx = -1
    for i, line in enumerate(row_lines):
        # Skip statement, advertiser, and ID lines
        if re.match(r'^(ST\d+|\d{2}[A-Z]+.*Prakit|\d{10,})$', line.strip()):
            continue
        # Found start of campaign name
        if line.strip() and not re.match(r'^\d+$', line.strip()):
            start_idx = i
            break
    
    if start_idx >= 0:
        campaign_parts = []
        for i in range(start_idx, len(row_lines)):
            line = row_lines[i].strip()
            # Stop at country, date, or amount
            if re.match(r'^(TH|US|SG|JP|KR)$', line) or re.match(r'^\d{4}-\d{2}', line) or re.search(r'\d+\.\d{2}', line):
                break
            if line:
                campaign_parts.append(line)
        
        return ' '.join(campaign_parts)
    
    return 'Unknown Campaign'

def extract_amount_from_row(full_text):
    """Extract amount from row text"""
    
    amount = 0
    
    # Pattern 1: Concatenated amounts (Total+Voucher+Cash without spaces)
    concat_pattern = r'(\d{1,3}(?:,\d{3})*\.\d{2})0\.00(\d{1,3}(?:,\d{3})*\.\d{2})'
    concat_match = re.search(concat_pattern, full_text)
    
    if concat_match:
        try:
            cash_amount = float(concat_match.group(2).replace(',', ''))
            amount = cash_amount
        except ValueError:
            amount = 0
    else:
        # Pattern 2: Spaced amounts
        spaced_pattern = r'(\d{1,3}(?:,\d{3})*\.\d{2})\s+(0\.00)\s+(\d{1,3}(?:,\d{3})*\.\d{2})'
        spaced_match = re.search(spaced_pattern, full_text)
        
        if spaced_match:
            try:
                cash_amount = float(spaced_match.group(3).replace(',', ''))
                amount = cash_amount
            except ValueError:
                amount = 0
    
    return amount

def parse_ap_campaign_pattern_v2(campaign_name):
    """
    Parse AP campaign pattern v2 - improved parsing
    
    Handles patterns like:
    pk|SDH_pk_40065_th-single-detached-house-centro-vibhavadi_none_View_tiktok_Boostpost_FBViewY25-JUN25-SDH-31_[ST]|1359G01
    pk|OnlineMKT_pk_AP-PawLiving-Content_none_Engagement_tiktok_Boostpost_TT-Paw-Post2-Jun_[ST]|1951A02
    pk|CD_pk_60029|CD_pk_th-condominium-rhythm-ekkamai-estate_none_Traffic_tiktok_VDO_TTQ2Y25-JUN25-APCD-NO2_[ST]|1972P04
    """
    
    components = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown',
        'period': 'Unknown',
        'campaign_id': 'Unknown',
        'description': campaign_name
    }
    
    if not campaign_name or not campaign_name.startswith('pk|'):
        return components
    
    # Extract campaign_id first (after [ST]| marker)
    if '[ST]|' in campaign_name:
        st_split = campaign_name.split('[ST]|')
        if len(st_split) > 1:
            campaign_id_part = st_split[1].strip()
            # Extract just the campaign ID, removing any trailing data
            id_match = re.match(r'([A-Z0-9]+)', campaign_id_part)
            if id_match:
                components['campaign_id'] = id_match.group(1)
        # Work with the part before [ST]
        main_pattern = st_split[0] + '[ST]'
    else:
        main_pattern = campaign_name
    
    # Split by pipes
    parts = main_pattern.split('|')
    
    if len(parts) >= 2:
        # Determine pattern type and extract content
        second_part = parts[1]
        third_part = parts[2] if len(parts) > 2 else ''
        
        # Pattern Type A: pk|40044|content... (numeric project ID)
        if re.match(r'^\d+$', second_part):
            components['project_id'] = second_part
            main_content = third_part
            
        # Pattern Type B: pk|CD_pk_60029|CD_pk_content... (prefix with ID, repeated pattern)
        elif len(parts) > 2 and ('CD_pk_' in second_part or 'SDH_pk_' in second_part):
            # Extract ID from second part
            id_match = re.search(r'(\d{5})', second_part)
            if id_match:
                components['project_id'] = id_match.group(1)
            # Main content is in third part
            main_content = third_part
            
        # Pattern Type C: pk|OnlineMKT_pk_content... (OnlineMKT)
        elif 'OnlineMKT' in second_part:
            components['project_id'] = 'OnlineMKT'
            main_content = second_part
            
        # Pattern Type D: pk|Corporate_pk_content... (Corporate)
        elif 'Corporate' in second_part:
            components['project_id'] = 'Corporate'
            main_content = second_part
            
        # Pattern Type E: pk|SDH_pk_40065_content... (all in second part)
        else:
            # Extract numeric ID
            id_match = re.search(r'(\d{5})', second_part)
            if id_match:
                components['project_id'] = id_match.group(1)
            main_content = second_part
        
        # Parse main content
        if main_content:
            # Extract project name
            if 'OnlineMKT_pk_' in main_content:
                # Pattern: OnlineMKT_pk_AP-PawLiving-Content_none...
                name_match = re.search(r'OnlineMKT_pk_([^_]+?)(?:_none|_)', main_content)
                if name_match:
                    components['project_name'] = name_match.group(1)
            elif 'Corporate_pk_Corporate' in main_content:
                components['project_name'] = 'Corporate'
            else:
                # Extract project name from various patterns
                patterns = [
                    # Standard patterns
                    r'pk_th-([a-zA-Z\-]+?)_none',
                    r'pk_([a-zA-Z\-]+?)_none',
                    r'th-([a-zA-Z\-]+?)_none',
                    # Full name patterns
                    r'(th-single-detached-house-[a-zA-Z\-]+?)_none',
                    r'(th-condominium-[a-zA-Z\-]+?)_none',
                    r'(single-detached-house-[a-zA-Z\-]+?)_none',
                    r'(condominium-[a-zA-Z\-]+?)_none',
                ]
                
                for pattern in patterns:
                    name_match = re.search(pattern, main_content)
                    if name_match:
                        components['project_name'] = name_match.group(1)
                        break
            
            # Extract objective
            objectives = ['View', 'Traffic', 'Awareness', 'Engagement', 'VDO-View']
            for obj in objectives:
                if f'_none_{obj}_' in main_content or f'_{obj}_' in main_content:
                    components['objective'] = obj.replace('VDO-View', 'View')
                    break
            
            # Extract period - improved patterns
            period_patterns = [
                # Standard patterns
                (r'Y\d{2}-([A-Z]{3}\d{2})', 0),      # Y25-JUN25
                (r'(Q\d{1}Y\d{2})', 0),               # Q2Y25
                (r'TT(?:TRAFFIC)?Q(\d{1}Y\d{2})', 1), # TTQ2Y25 or TTTRAFFICQ2Y25
                (r'-([A-Z]{3}\d{2})-', 1),           # -JUN25-
                (r'_TT-[^-]+-[^-]+-([A-Z][a-z]{2})_', 1),  # TT-Paw-Post2-Jun
                (r'-([A-Z][a-z]{2})\d*_\[ST\]', 1),  # -Jun25_[ST] or -Jun_[ST]
                (r'_([A-Z][a-z]{2})_\[ST\]', 1),     # _Jun_[ST]
            ]
            
            for pattern, group in period_patterns:
                period_match = re.search(pattern, main_content)
                if period_match:
                    extracted = period_match.group(group) if group else period_match.group(0)
                    # Clean up period
                    if extracted.startswith('TT'):
                        extracted = re.sub(r'TT(?:TRAFFIC)?', '', extracted)
                    components['period'] = extracted
                    break
    
    return components

def create_tiktok_ap_record(row_data, base_fields):
    """Create AP record with detailed fields parsed from campaign name"""
    
    if not row_data or row_data.get('amount', 0) <= 0:
        return None
    
    campaign_name = row_data.get('campaign_name', '')
    
    # Parse AP campaign pattern with improved parser
    ap_components = parse_ap_campaign_pattern_v2(campaign_name)
    
    record = {
        **base_fields,
        'invoice_type': 'AP',
        'agency': ap_components['agency'],
        'project_id': ap_components['project_id'],
        'project_name': ap_components['project_name'],
        'objective': ap_components['objective'],
        'period': ap_components['period'],
        'campaign_id': ap_components['campaign_id'],
        'description': ap_components['description'],
        'amount': row_data.get('amount', 0),
        'target_country': row_data.get('target_country', 'TH'),
        'statement_id': row_data.get('statement_id', 'Unknown')
    }
    
    return record

def create_tiktok_non_ap_record(row_data, base_fields):
    """Create Non-AP record using full campaign name as description"""
    
    if not row_data or row_data.get('amount', 0) <= 0:
        return None
    
    # Use the full campaign name as description
    campaign_name = row_data.get('campaign_name', 'Unknown Campaign')
    
    record = {
        **base_fields,
        'invoice_type': 'Non-AP',
        'description': campaign_name,
        'amount': row_data.get('amount', 0)
    }
    
    return record

def extract_tiktok_invoice_info(lines):
    """Extract basic TikTok invoice information"""
    
    info = {}
    
    for line in lines:
        line_clean = line.strip()
        
        # Extract invoice number (THTT format)
        if 'Invoice No.' in line or 'THTT' in line:
            invoice_match = re.search(r'THTT\d+', line_clean)
            if invoice_match:
                info['invoice_number'] = invoice_match.group(0)
        
        # Extract invoice date
        if 'Invoice Date' in line:
            date_match = re.search(r'(\d{2}/\d{2}/\d{4}|\d{1,2}\s+\w+,?\s+\d{4})', line_clean)
            if date_match:
                info['invoice_date'] = date_match.group(1)
        
        # Extract contract number
        if 'Contract No.' in line:
            contract_match = re.search(r'Contract No\.\s*([A-Z0-9]+)', line_clean)
            if contract_match:
                info['contract_number'] = contract_match.group(1)
    
    return info

def determine_tiktok_invoice_type_enhanced(text_content):
    """Enhanced TikTok invoice type detection - AP requires BOTH ST pattern AND pk| pattern"""
    
    # Check for ST patterns (ST followed by numbers)
    has_st_pattern = bool(re.search(r'ST\d{5,}', text_content))
    
    # Check for pk| patterns 
    has_pk_pattern = 'pk|' in text_content
    
    # AP invoices must have BOTH ST pattern AND pk| pattern
    if has_st_pattern and has_pk_pattern:
        return "AP"
    else:
        return "Non-AP"

def find_tiktok_invoice_total(lines, filename):
    """Find TikTok invoice total"""
    
    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()
        
        if 'total amount due' in line_lower:
            amounts = re.findall(r'[\d,]+\.\d{2}', line_clean)
            if amounts:
                try:
                    return float(amounts[-1].replace(',', ''))
                except:
                    continue
    
    return 0

if __name__ == "__main__":
    print("Final Improved TikTok Parser v2")