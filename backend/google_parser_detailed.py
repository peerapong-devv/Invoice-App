#!/usr/bin/env python3
"""
Google parser with detailed data extraction for both AP and Non-AP invoices
"""

import re
from typing import Dict, List, Any

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice with detailed extraction"""
    
    # Determine invoice type
    has_pk_pattern = 'pk|' in text_content and '[ST]|' in text_content
    has_invalid_activity = 'กิจกรรมที่ไม่ถูกต้อง' in text_content or 'Invalid activity' in text_content
    
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
    
    # Check if this is an AP invoice with line items
    if has_pk_pattern or has_invalid_activity:
        items = extract_google_detailed_items(text_content, base_fields)
        if items:
            return items
    
    # Otherwise treat as Non-AP
    return extract_google_non_ap_items(text_content, base_fields)

def extract_google_detailed_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract detailed Google items from invoice"""
    
    items = []
    lines = text_content.split('\n')
    
    # Look for line items with pk| patterns
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for pk| pattern
        if 'pk|' in line and '[ST]|' in line:
            # Extract the full pattern
            pk_match = re.search(r'(pk\|[^\s]+\[ST\]\|[A-Z0-9]+)', line)
            if pk_match:
                pk_pattern = pk_match.group(1)
                
                # Look for amount in next few lines
                amount = 0.0
                quantity = 0
                unit = ''
                
                for j in range(i, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    
                    # Check for quantity and unit (e.g., "50277 การคลิก")
                    qty_match = re.match(r'^(\d+)\s+(\S+)', next_line)
                    if qty_match:
                        try:
                            quantity = int(qty_match.group(1))
                            unit = qty_match.group(2)
                        except:
                            pass
                    
                    # Check for amount
                    amt_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$', next_line)
                    if amt_match and j > i:
                        try:
                            amount = float(amt_match.group(1).replace(',', ''))
                            break
                        except:
                            pass
                
                if amount > 0:
                    # Parse AP fields
                    ap_fields = parse_google_ap_fields(pk_pattern)
                    
                    item = {
                        **base_fields,
                        'invoice_type': 'AP',
                        'line_number': len(items) + 1,
                        'amount': amount,
                        'total': amount,
                        'description': pk_pattern,
                        'quantity': quantity,
                        'unit': unit,
                        **ap_fields
                    }
                    items.append(item)
        
        # Check for invalid activity (credit/adjustment)
        elif 'กิจกรรมที่ไม่ถูกต้อง' in line or 'Invalid activity' in line:
            # Look for negative amount in next few lines
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                neg_match = re.match(r'^-(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$', next_line)
                if neg_match:
                    try:
                        amount = -float(neg_match.group(1).replace(',', ''))
                        
                        # Extract campaign info from the line
                        campaign_match = re.search(r'pk\|[^\s,]+', line)
                        if campaign_match:
                            pk_pattern = campaign_match.group(0)
                            # Add [ST] if missing for proper parsing
                            if '[ST]' not in pk_pattern:
                                pk_pattern = pk_pattern.replace('_...', '[ST]|CREDIT')
                            ap_fields = parse_google_ap_fields(pk_pattern)
                        else:
                            ap_fields = {
                                'agency': 'pk',
                                'project_id': 'Adjustment',
                                'project_name': 'Credit/Adjustment',
                                'objective': 'N/A',
                                'period': 'N/A',
                                'campaign_id': 'CREDIT'
                            }
                        
                        item = {
                            **base_fields,
                            'invoice_type': 'AP',
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': f'Credit adjustment: {line[:100]}',
                            **ap_fields
                        }
                        items.append(item)
                        break
                    except:
                        pass
        
        i += 1
    
    # If we found items, mark as AP
    if items:
        return sorted(items, key=lambda x: x.get('line_number', 999))
    
    return []

def extract_google_non_ap_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Google Non-AP items with account details"""
    
    # Look for total amount in various formats
    total_amount = 0.0
    
    # Pattern 1: จำนวนเงินรวมที่ต้องชำระในสกุลเงิน THB (may have negative)
    total_match = re.search(r'จำนวนเงินรวมที่ต้องชำระในสกุลเงิน\s+THB\s*(-?฿?[\d,]+\.?\d*)', text_content)
    if not total_match:
        # Pattern 2: ยอดรวมในสกุลเงิน THB  
        total_match = re.search(r'ยอดรวมในสกุลเงิน\s+THB\s*(-?฿?[\d,]+\.?\d*)', text_content)
    if not total_match:
        # Pattern 3: Total amount in THB
        total_match = re.search(r'Total amount.*THB.*?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
    
    if total_match:
        try:
            amount_str = total_match.group(1)
            # Handle negative sign
            if amount_str.startswith('-'):
                total_amount = -float(amount_str[1:].replace('฿', '').replace(',', ''))
            else:
                total_amount = float(amount_str.replace('฿', '').replace(',', ''))
        except:
            pass
    
    # Extract account details
    account_name = 'Google Ads'
    account_match = re.search(r'บัญชี:\s*([^\n]+)', text_content)
    if account_match:
        account_name = account_match.group(1).strip()
    
    # Extract billing period
    period = ''
    period_match = re.search(r'(\d{1,2}\s+\S+\s+\d{4})\s*-\s*(\d{1,2}\s+\S+\s+\d{4})', text_content)
    if period_match:
        period = f"{period_match.group(1)} - {period_match.group(2)}"
    
    # Create single item with total and details
    item = {
        **base_fields,
        'invoice_type': 'Non-AP',
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
    pattern = re.sub(r'\s+', ' ', pattern.replace('\n', ' ').strip())
    
    # Extract campaign_id (after [ST]|)
    if '[ST]|' in pattern:
        parts = pattern.split('[ST]|')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            # Extract just the ID
            campaign_id_match = re.match(r'^([A-Z0-9]+)', campaign_id)
            if campaign_id_match:
                result['campaign_id'] = campaign_id_match.group(1)
        pattern = parts[0]  # Work with part before [ST]
    
    # Split by pipes
    parts = pattern.split('|')
    
    if len(parts) >= 2:
        # Project ID is usually second part
        project_id = parts[1]
        if project_id.isdigit():
            result['project_id'] = project_id
        elif project_id in ['Corporate', 'OnlineMKT']:
            result['project_id'] = project_id
            result['project_name'] = 'Corporate' if project_id == 'Corporate' else 'Online Marketing'
        
        # Join remaining parts for details
        if len(parts) > 2:
            details = '|'.join(parts[2:])
            
            # Extract project type/name
            if 'SDH' in details or 'single-detached-house' in details:
                result['project_name'] = 'Single Detached House'
            elif 'TH' in details or 'townhome' in details.lower():
                result['project_name'] = 'Townhome'
            elif 'CD' in details or 'condominium' in details:
                result['project_name'] = 'Condominium'
            
            # Extract specific project names
            project_names = {
                'centro': 'Centro',
                'moden': 'Moden',
                'palazzo': 'The Palazzo',
                'pleno': 'Pleno',
                'town-avenue': 'Town Avenue',
                'the-city': 'The City',
                'life': 'Life',
                'apitown': 'Apitown',
                'bangyai': 'Bangyai',
                'ratchapruek': 'Ratchapruek',
                'nontaburi': 'Nontaburi'
            }
            
            for key, name in project_names.items():
                if key in details.lower():
                    if result['project_name'] in ['Single Detached House', 'Townhome', 'Condominium']:
                        result['project_name'] = f"{result['project_name']} - {name}"
                    else:
                        result['project_name'] = name
                    break
            
            # Extract objective
            objectives = ['Awareness', 'Conversion', 'LeadAd', 'Traffic', 'Engagement', 'View', 'Responsive']
            for obj in objectives:
                if obj in details:
                    result['objective'] = obj
                    break
            
            # Extract period from patterns like GDNQ2Y25
            period_patterns = [
                r'GDN(Q[1-4]Y\d{2})',      # GDNQ2Y25
                r'FB(Q[1-4]Y\d{2})',        # FBQ2Y25
                r'(Q[1-4]Y\d{2})',          # Q2Y25
                r'([A-Z]{3}\d{2})',          # JUN25
            ]
            
            for pattern_re in period_patterns:
                period_match = re.search(pattern_re, details)
                if period_match:
                    result['period'] = period_match.group(1)
                    break
    
    return result

if __name__ == "__main__":
    print("Google Parser with Detailed Extraction - Ready")