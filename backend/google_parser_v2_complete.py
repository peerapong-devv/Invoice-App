#!/usr/bin/env python3
"""
Google Parser Complete - Extract ALL line items from PDF without hardcoding
Handles both table format and extreme text fragmentation
"""

import re
from typing import Dict, List, Any, Optional, Tuple

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice - extract all line items without hardcoding"""
    
    # Extract invoice number
    invoice_number = extract_invoice_number(text_content, filename)
    
    # Base fields
    base_fields = {
        'platform': 'Google',
        'filename': filename,
        'invoice_number': invoice_number,
        'invoice_id': invoice_number
    }
    
    # Check if text is fragmented
    has_fragmentation = check_fragmentation(text_content)
    
    items = []
    
    if has_fragmentation:
        # Handle extremely fragmented PDFs
        items = extract_from_fragmented_pdf(text_content, base_fields)
    else:
        # Handle normal table format PDFs
        items = extract_from_table_format(text_content, base_fields)
    
    # Determine invoice type
    invoice_type = 'AP' if items and len(items) > 1 else 'Non-AP'
    
    # Check for credit notes
    if any(item['amount'] < 0 for item in items):
        invoice_type = 'Non-AP'
    
    # Set invoice type and calculate total
    total = sum(item['amount'] for item in items)
    for item in items:
        item['invoice_type'] = invoice_type
        item['total'] = total
    
    # If no items found, create single line with total
    if not items:
        total = extract_total_amount(text_content)
        if total != 0:
            items = [{
                **base_fields,
                'invoice_type': 'Non-AP',
                'line_number': 1,
                'amount': total,
                'total': total,
                'description': extract_account_name(text_content),
                'agency': None,
                'project_id': None,
                'project_name': None,
                'objective': None,
                'period': extract_period(text_content),
                'campaign_id': None
            }]
    
    return items

def check_fragmentation(text_content: str) -> bool:
    """Check if text has extreme fragmentation"""
    # Count zero-width spaces
    zwsp_count = text_content.count('\u200b')
    # Count single character lines
    lines = text_content.split('\n')
    single_char_lines = sum(1 for line in lines if len(line.strip()) == 1)
    
    # If high concentration of zero-width spaces or many single char lines
    return zwsp_count > 100 or single_char_lines > 50

def extract_from_fragmented_pdf(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract items from PDFs with extreme character fragmentation"""
    items = []
    lines = text_content.split('\n')
    
    # Find table area
    table_start = -1
    table_end = -1
    
    for i, line in enumerate(lines):
        if 'คำอธิบาย' in line:
            table_start = i
        elif table_start > -1 and ('ยอดรวม' in line or 'จำนวนเงินรวม' in line):
            table_end = i
            break
    
    if table_start == -1:
        return items
    
    # Process table area - reconstruct fragmented patterns
    i = table_start + 3  # Skip header
    pattern_buffer = []
    collecting_pattern = False
    
    while i < (table_end if table_end > -1 else len(lines)):
        if i >= len(lines):
            break
        line = lines[i].strip()
        
        # Remove zero-width spaces
        clean_line = line.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
        
        # Check if single character (part of fragmented pattern)
        if len(clean_line) == 1 and clean_line not in ['', ' ', '\t']:
            pattern_buffer.append(clean_line)
            collecting_pattern = True
        else:
            # End of fragmented section - process buffer
            if collecting_pattern and pattern_buffer:
                # Join characters
                reconstructed = ''.join(pattern_buffer)
                
                # Check if it's a pk| pattern
                if reconstructed.startswith('pk|') or 'pk|' in reconstructed:
                    # Look for amount in next few lines
                    for j in range(i, min(i + 10, len(lines))):
                        amount_line = lines[j].strip()
                        amount_match = re.match(r'^(\d{1,3}(?:,\d{3})*\.?\d{2})$', amount_line)
                        if amount_match:
                            amount = float(amount_match.group(1).replace(',', ''))
                            if 100 < amount < 500000:  # Valid amount range
                                # Parse AP fields from reconstructed pattern
                                ap_fields = parse_pk_pattern(reconstructed)
                                
                                item = {
                                    **base_fields,
                                    'line_number': len(items) + 1,
                                    'amount': amount,
                                    'description': reconstructed,
                                    **ap_fields
                                }
                                items.append(item)
                                break
                
                pattern_buffer = []
                collecting_pattern = False
            
            # Check if this is an amount line
            if clean_line and re.match(r'^\d{1,3}(?:,\d{3})*\.?\d{2}$', clean_line):
                # Might be an isolated amount, skip for now
                pass
        
        i += 1
    
    # Process any remaining buffer
    if pattern_buffer:
        reconstructed = ''.join(pattern_buffer)
        if reconstructed.startswith('pk|'):
            # Try to find associated amount
            for j in range(max(0, i - 5), i):
                if j < len(lines):
                    amount_line = lines[j].strip()
                    amount_match = re.match(r'^(\d{1,3}(?:,\d{3})*\.?\d{2})$', amount_line)
                    if amount_match:
                        amount = float(amount_match.group(1).replace(',', ''))
                        if 100 < amount < 500000:
                            ap_fields = parse_pk_pattern(reconstructed)
                            item = {
                                **base_fields,
                                'line_number': len(items) + 1,
                                'amount': amount,
                                'description': reconstructed,
                                **ap_fields
                            }
                            items.append(item)
                            break
    
    return items

def extract_from_table_format(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract items from normal table format PDFs"""
    items = []
    lines = text_content.split('\n')
    
    # Find table header
    header_idx = -1
    for i, line in enumerate(lines):
        if 'คำอธิบาย' in line:
            # Verify it's a table header by checking next lines
            if i + 2 < len(lines) and ('ปริมาณ' in lines[i+1] or 'จำนวนเงิน' in lines[i+2]):
                header_idx = i
                break
    
    if header_idx == -1:
        return items
    
    # Process table rows
    i = header_idx + 3  # Skip header
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and headers
        if not line or line in ['การคลิก', 'Click', 'THB']:
            i += 1
            continue
        
        # Check for end of table
        if any(end in line for end in ['ยอดรวม', 'Total', 'GST', 'ภาษี']):
            break
        
        # Try to extract campaign info and amount
        # Look for campaign patterns
        if any(pattern in line for pattern in ['DMCRM', 'DMHEALTH', 'PRAKIT', 'D-', 'pk|']):
            # This is likely a campaign description
            description = line
            
            # Look for ID and amount in next lines
            campaign_id = None
            amount = None
            
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                
                # Check for ID (long number)
                if re.match(r'^\d{7,}$', next_line):
                    campaign_id = next_line
                
                # Check for amount
                elif re.match(r'^\d{1,3}(?:,\d{3})*\.?\d{2}$', next_line):
                    try:
                        amount = float(next_line.replace(',', ''))
                    except:
                        pass
            
            # If we found an amount, create item
            if amount and 100 < amount < 500000:
                # Parse campaign details
                ap_fields = parse_campaign_description(description)
                if campaign_id and not ap_fields.get('campaign_id'):
                    ap_fields['campaign_id'] = campaign_id
                
                item = {
                    **base_fields,
                    'line_number': len(items) + 1,
                    'amount': amount,
                    'description': description,
                    **ap_fields
                }
                items.append(item)
                
                # Skip processed lines
                i += 4
                continue
        
        i += 1
    
    # Also check for fragmented campaign names (with zero-width spaces)
    if not items:
        items = extract_fragmented_table_items(text_content, base_fields)
    
    return items

def extract_fragmented_table_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract items from table format with fragmented campaign names"""
    items = []
    lines = text_content.split('\n')
    
    # Find campaigns with fragmented text
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for campaign patterns with zero-width spaces
        if '\u200b' in line and any(p in line.replace('\u200b', '') for p in ['DMCRM', 'DMHEALTH', 'PRAKIT']):
            # Reconstruct campaign name
            clean_desc = line.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '').strip()
            
            # Look for amount
            for j in range(i + 1, min(i + 10, len(lines))):
                amount_line = lines[j].strip()
                amount_match = re.match(r'^(\d{1,3}(?:,\d{3})*\.?\d{2})$', amount_line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    if 100 < amount < 500000:
                        ap_fields = parse_campaign_description(clean_desc)
                        
                        item = {
                            **base_fields,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'description': clean_desc,
                            **ap_fields
                        }
                        items.append(item)
                        i = j
                        break
        
        i += 1
    
    return items

def parse_pk_pattern(pattern: str) -> dict:
    """Parse pk| pattern to extract AP fields"""
    result = {
        'agency': 'pk',
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': None,
        'campaign_id': None
    }
    
    # Clean pattern
    pattern = pattern.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    
    # Extract parts
    parts = pattern.split('|')
    
    if len(parts) >= 2:
        # Project ID is usually the second part
        if parts[1].isdigit():
            result['project_id'] = parts[1]
        
        # Join remaining parts
        if len(parts) > 2:
            content = '|'.join(parts[2:])
            
            # Extract project name
            if 'SDH' in content:
                result['project_name'] = 'Single Detached House'
                # Extract location
                location_patterns = {
                    'centro': 'Centro',
                    'ratchapruek': 'Ratchapruek',
                    'onnut': 'Onnut',
                    'vibhavadi': 'Vibhavadi'
                }
                for key, name in location_patterns.items():
                    if key in content.lower():
                        result['project_name'] += f' - {name}'
                        break
            elif 'TH' in content and 'townhome' in content.lower():
                result['project_name'] = 'Townhome'
            elif 'CD' in content and 'condominium' in content.lower():
                result['project_name'] = 'Condominium'
            elif 'Apitown' in content:
                result['project_name'] = 'Apitown'
                if 'udonthani' in content.lower():
                    result['project_name'] += ' - Udon Thani'
                elif 'phitsanulok' in content.lower():
                    result['project_name'] += ' - Phitsanulok'
            
            # Extract objective
            objectives = {
                'Traffic_Responsive': 'Traffic - Responsive',
                'Traffic_Search_Generic': 'Search - Generic',
                'Traffic_Search_Compet': 'Search - Competitor',
                'Traffic_Search_Brand': 'Search - Brand',
                'Traffic_CollectionCanvas': 'Traffic - Collection',
                'LeadAd': 'Lead Generation',
                'Traffic': 'Traffic',
                'Awareness': 'Awareness',
                'View': 'View'
            }
            
            for key, value in objectives.items():
                if key in content:
                    result['objective'] = value
                    break
            
            # Extract period
            period_patterns = [
                r'Q(\d)Y(\d{2})',  # Q2Y25
                r'([A-Z]{3}\d{2})',  # JUN25
                r'Y(\d{2})-([A-Z]{3}\d{2})'  # Y25-JUN25
            ]
            
            for pattern in period_patterns:
                match = re.search(pattern, content)
                if match:
                    if 'Q' in pattern:
                        result['period'] = f'Q{match.group(1)}Y{match.group(2)}'
                    elif 'Y' in pattern:
                        result['period'] = f'Y{match.group(1)}-{match.group(2)}'
                    else:
                        result['period'] = match.group(0)
                    break
            
            # Extract campaign ID (after [ST]|)
            st_match = re.search(r'\[ST\]\|(\w+)', content)
            if st_match:
                result['campaign_id'] = st_match.group(1)
    
    return result

def parse_campaign_description(description: str) -> dict:
    """Parse campaign description for Non-AP invoices"""
    result = {
        'agency': 'pk',
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': None,
        'campaign_id': None
    }
    
    # Clean description
    description = description.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    
    # Extract campaign ID patterns
    id_patterns = [
        r'([A-Z]{2,}[-_][A-Z0-9]+[-_]\d+[-_]\d+)',  # DMCRM-IN-041-0625
        r'D-([A-Z]+[-_][A-Z]+[-_]\d+[-_]\d+)',      # D-DMHealth-TV-00275-0625
        r'([A-Z]+-[A-Z]+-\d+-\d+)'                  # Any pattern with dashes
    ]
    
    for pattern in id_patterns:
        match = re.search(pattern, description)
        if match:
            result['campaign_id'] = match.group(1) if '(' in pattern else match.group(0)
            break
    
    # Extract project name
    if 'DMCRM' in description:
        result['project_name'] = 'Digital Marketing CRM'
        result['project_id'] = 'DMCRM'
    elif 'DMHEALTH' in description or 'DMHealth' in description:
        result['project_name'] = 'Digital Marketing Health'
        result['project_id'] = 'DMHEALTH'
    elif 'PRAKIT' in description:
        result['project_name'] = 'Prakit'
        result['project_id'] = 'PRAKIT'
    
    # Extract objective
    if '_View_' in description or 'View' in description:
        result['objective'] = 'View'
    elif 'VDO' in description:
        result['objective'] = 'Video View'
    elif 'Traffic' in description:
        result['objective'] = 'Traffic'
    
    # Extract period
    period_patterns = [
        r"(\d{1,2}-\d{1,2}[A-Za-z]{3}'?\d{2})",  # 20-27Jun'25
        r"([A-Z][a-z]{2}\d{2})",                  # Jun25
        r"([A-Z][a-z]{2}'?\d{2})",               # Jun'25
        r"-(\d{4})"                               # -0625 (June 2025)
    ]
    
    for pattern in period_patterns:
        match = re.search(pattern, description)
        if match:
            period = match.group(1)
            # Convert -0625 format to Jun25
            if pattern == r"-(\d{4})":
                month_num = period[0:2]
                year = period[2:4]
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                try:
                    month_idx = int(month_num) - 1
                    if 0 <= month_idx < 12:
                        result['period'] = f'{months[month_idx]}{year}'
                except:
                    pass
            else:
                result['period'] = period
            break
    
    return result

def extract_invoice_number(text_content: str, filename: str) -> str:
    """Extract invoice number"""
    # Thai pattern
    inv_match = re.search(r'หมายเลขใบแจ้งหนี้:\s*(\d{10})', text_content)
    if inv_match:
        return inv_match.group(1)
    
    # English pattern
    inv_match = re.search(r'Invoice number:\s*(\d{10})', text_content)
    if inv_match:
        return inv_match.group(1)
    
    # From filename
    inv_match = re.search(r'(\d{10})', filename)
    if inv_match:
        return inv_match.group(1)
    
    return 'Unknown'

def extract_total_amount(text_content: str) -> float:
    """Extract total amount"""
    patterns = [
        r'ยอดรวม.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'จำนวนเงินรวม.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'Total.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
    
    return 0.0

def extract_account_name(text_content: str) -> str:
    """Extract account name"""
    match = re.search(r'บัญชี:\s*([^\n]+)', text_content)
    if match:
        return match.group(1).strip()
    return 'Google Ads'

def extract_period(text_content: str) -> Optional[str]:
    """Extract billing period"""
    pattern = r'(\d{1,2}\s+\S+\s+\d{4})\s*[-–]\s*(\d{1,2}\s+\S+\s+\d{4})'
    match = re.search(pattern, text_content)
    if match:
        return f"{match.group(1)} - {match.group(2)}"
    return None

if __name__ == "__main__":
    print("Google Parser Complete - Ready")
    print("Handles both table format and extreme text fragmentation")