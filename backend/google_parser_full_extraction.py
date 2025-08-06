#!/usr/bin/env python3
"""
Google parser with complete line item extraction
Handles AP invoices with pk| patterns, credits, and fees
"""

import re
from typing import Dict, List, Any

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice with complete extraction"""
    
    # Extract invoice number
    invoice_number = filename.replace('.pdf', '') if filename else 'Unknown'
    inv_match = re.search(r'หมายเลขใบแจ้งหนี้:\s*(\d+)', text_content)
    if not inv_match:
        inv_match = re.search(r'Invoice number:\s*(\d+)', text_content)
    if inv_match:
        invoice_number = inv_match.group(1)
    
    # Base fields
    base_fields = {
        'platform': 'Google',
        'filename': filename,
        'invoice_number': invoice_number,
        'invoice_id': invoice_number
    }
    
    # Check if this is AP by looking for pk| patterns
    has_pk_pattern = bool(re.search(r'pk\|[^|]+\|', text_content))
    
    if has_pk_pattern:
        # AP invoice - extract all line items
        items = extract_google_ap_detailed(text_content, base_fields)
        invoice_type = 'AP'
    else:
        # Non-AP invoice
        items = extract_google_non_ap(text_content, base_fields)
        invoice_type = 'Non-AP'
    
    # Set invoice type for all items
    for item in items:
        item['invoice_type'] = invoice_type
    
    return items

def extract_google_ap_detailed(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract all Google AP line items including credits and fees"""
    
    items = []
    lines = text_content.split('\n')
    
    # Process line by line
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Pattern 1: pk| lines with amount on same or next line
        if 'pk|' in line and '[ST' in line:
            # Extract the pk pattern
            pk_match = re.search(r'(pk\|[^\]]+\])', line)
            if pk_match:
                pk_pattern = pk_match.group(1)
                
                # Add |campaign_id if it's on the next line
                if ']|' not in pk_pattern and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r'^\|[A-Z0-9]+', next_line):
                        pk_pattern += next_line
                
                # Look for quantity and amount
                quantity = 0
                unit = ''
                amount = 0.0
                
                # Check same line for amount at end
                amount_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$', line)
                if amount_match:
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                    except:
                        pass
                
                # Look ahead for quantity and amount pattern
                j = i + 1
                while j < len(lines) and j <= i + 3:
                    check_line = lines[j].strip()
                    
                    # Pattern: "25297 การคลิก 9,895.90"
                    full_match = re.match(r'^(\d+)\s+(\S+)\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$', check_line)
                    if full_match:
                        try:
                            quantity = int(full_match.group(1))
                            unit = full_match.group(2)
                            amount = float(full_match.group(3).replace(',', ''))
                            break
                        except:
                            pass
                    
                    # Just amount on line
                    elif re.match(r'^(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$', check_line):
                        try:
                            amount = float(check_line.replace(',', ''))
                            break
                        except:
                            pass
                    
                    j += 1
                
                if amount != 0:
                    # Parse AP fields
                    ap_fields = parse_google_ap_fields(pk_pattern)
                    
                    item = {
                        **base_fields,
                        'line_number': len(items) + 1,
                        'amount': amount,
                        'total': amount,
                        'description': pk_pattern,
                        'quantity': quantity,
                        'unit': unit,
                        **ap_fields
                    }
                    items.append(item)
        
        # Pattern 2: Credit lines (negative amounts)
        elif 'กิจกรรมที่ไม่ถูกต้อง' in line:
            # Look for negative amount after this line
            j = i + 1
            while j < len(lines) and j <= i + 3:
                check_line = lines[j].strip()
                
                # Check for negative amount
                neg_match = re.match(r'^-(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$', check_line)
                if neg_match:
                    try:
                        amount = -float(neg_match.group(1).replace(',', ''))
                        
                        # Try to extract campaign from credit description
                        credit_desc = line
                        if j + 1 < len(lines):
                            next_desc = lines[j + 1].strip()
                            if 'pk|' in next_desc:
                                credit_desc += ' ' + next_desc
                        
                        # Extract pk pattern from description
                        pk_match = re.search(r'(pk\|[^,\s]+)', credit_desc)
                        if pk_match:
                            pk_pattern = pk_match.group(1)
                            ap_fields = parse_google_ap_fields(pk_pattern)
                        else:
                            ap_fields = {
                                'agency': 'pk',
                                'project_id': 'Credit',
                                'project_name': 'Credit Adjustment',
                                'objective': 'N/A',
                                'period': 'N/A',
                                'campaign_id': 'CREDIT'
                            }
                        
                        item = {
                            **base_fields,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': credit_desc[:200],
                            **ap_fields
                        }
                        items.append(item)
                        break
                    except:
                        pass
                
                j += 1
        
        # Pattern 3: Fee lines
        elif 'ค่าธรรมเนียม' in line and 'สเปน' in line:
            # Spanish fee
            amount_match = re.search(r'(\d+\.?\d*)\s*$', line)
            if amount_match:
                try:
                    amount = float(amount_match.group(1))
                    if amount > 0:
                        item = {
                            **base_fields,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': 'ค่าธรรมเนียมในการดำเนินงานตามกฎระเบียบของประเทศสเปน',
                            'agency': None,
                            'project_id': 'Fee',
                            'project_name': 'Regulatory Fee - Spain',
                            'objective': None,
                            'period': None,
                            'campaign_id': None
                        }
                        items.append(item)
                except:
                    pass
        
        elif 'ค่าธรรมเนียม' in line and 'ฝรั่งเศส' in line:
            # French fee
            amount_match = re.search(r'(\d+\.?\d*)\s*$', line)
            if amount_match:
                try:
                    amount = float(amount_match.group(1))
                    if amount > 0:
                        item = {
                            **base_fields,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': 'ค่าธรรมเนียมในการดำเนินงานตามกฏระเบียบของประเทศฝรั่งเศส',
                            'agency': None,
                            'project_id': 'Fee',
                            'project_name': 'Regulatory Fee - France',
                            'objective': None,
                            'period': None,
                            'campaign_id': None
                        }
                        items.append(item)
                except:
                    pass
        
        i += 1
    
    return items

def extract_google_non_ap(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Google Non-AP invoice as single item with total"""
    
    # Extract total amount
    total_amount = 0.0
    
    # Pattern 1: จำนวนเงินรวมที่ต้องชำระในสกุลเงิน THB
    total_match = re.search(r'จำนวนเงินรวมที่ต้องชำระในสกุลเงิน\s+THB\s*[:\s]*(-?฿?[\d,]+\.?\d*)', text_content)
    if not total_match:
        # Pattern 2: ยอดรวมในสกุลเงิน THB  
        total_match = re.search(r'ยอดรวมในสกุลเงิน\s+THB\s*[:\s]*(-?฿?[\d,]+\.?\d*)', text_content)
    
    if total_match:
        try:
            amount_str = total_match.group(1)
            amount_str = amount_str.replace('฿', '').replace(',', '').strip()
            total_amount = float(amount_str)
        except:
            pass
    
    # Extract account info
    account_match = re.search(r'บัญชี:\s*([^\n]+)', text_content)
    account_name = account_match.group(1).strip() if account_match else 'Google Ads'
    
    # Extract period
    period_match = re.search(r'(\d{1,2}\s+\S+\s+\d{4})\s*-\s*(\d{1,2}\s+\S+\s+\d{4})', text_content)
    period = f"{period_match.group(1)} - {period_match.group(2)}" if period_match else ''
    
    item = {
        **base_fields,
        'line_number': 1,
        'description': f'{account_name}{f" ({period})" if period else ""}',
        'amount': total_amount,
        'total': total_amount,
        'agency': None,
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': period if period else None,
        'campaign_id': None
    }
    
    return [item]

def parse_google_ap_fields(pattern: str) -> Dict[str, str]:
    """Parse Google AP fields from pk| pattern"""
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown',
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    # Clean pattern
    pattern = re.sub(r'\s+', ' ', pattern.strip())
    
    # Extract campaign ID if present
    if '[ST]|' in pattern:
        parts = pattern.split('[ST]|')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            id_match = re.match(r'^([A-Z0-9]+)', campaign_id)
            if id_match:
                result['campaign_id'] = id_match.group(1)
        pattern = parts[0] + '[ST]'
    
    # Split by pipes
    parts = pattern.split('|')
    
    if len(parts) >= 2:
        # Project ID is usually second part
        project_id = parts[1]
        
        # Check if it's numeric
        if project_id.isdigit():
            result['project_id'] = project_id
        
        # Parse remaining content
        if len(parts) > 2:
            content = '|'.join(parts[2:])
            
            # Extract project name
            if 'Apitown' in content:
                result['project_name'] = 'Apitown'
                # Extract location
                if 'udonthani' in content.lower():
                    result['project_name'] = 'Apitown - Udonthani'
                elif 'udornthani' in content.lower():
                    result['project_name'] = 'Apitown - Udonthani'
            
            # Extract objective
            if '_Traffic_' in content:
                result['objective'] = 'Traffic'
                # Check for sub-types
                if '_Search_Generic' in content:
                    result['objective'] = 'Search - Generic'
                elif '_Search_Compet' in content:
                    result['objective'] = 'Search - Competitor'
                elif '_Search_Brand' in content:
                    result['objective'] = 'Search - Brand'
                elif '_Responsive' in content:
                    result['objective'] = 'Traffic'
            elif '_Awareness_' in content:
                result['objective'] = 'Awareness'
            elif '_Engagement_' in content:
                result['objective'] = 'Engagement'
    
    return result

if __name__ == "__main__":
    print("Google Full Extraction Parser - Ready")