#!/usr/bin/env python3
"""
Advanced Google parser that handles both text extraction and pattern matching
Similar quality to Facebook and TikTok parsers
"""

import re
from typing import Dict, List, Any
import fitz

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice with advanced extraction"""
    
    # Extract invoice number
    invoice_number = filename.replace('.pdf', '') if filename else 'Unknown'
    inv_match = re.search(r'หมายเลขใบแจ้งหนี้:\s*(\d+)', text_content)
    if not inv_match:
        inv_match = re.search(r'Invoice number:\s*(\d+)', text_content)
        if not inv_match:
            # Try extracting from filename
            inv_match = re.search(r'(\d{10})', filename)
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
    # Try different patterns since extraction may vary
    has_pk_pattern = bool(re.search(r'pk[|｜]', text_content)) or bool(re.search(r'pk\s*\|', text_content))
    
    if has_pk_pattern:
        # AP invoice - extract all line items
        items = extract_google_ap_comprehensive(text_content, base_fields)
        invoice_type = 'AP'
    else:
        # Non-AP invoice
        items = extract_google_non_ap(text_content, base_fields)
        invoice_type = 'Non-AP'
    
    # If no items found, create at least one with total
    if not items:
        total = extract_total_amount(text_content)
        if total != 0:
            items = [{
                **base_fields,
                'invoice_type': invoice_type,
                'line_number': 1,
                'amount': total,
                'total': total,
                'description': f'Google Ads {invoice_type} Invoice',
                'agency': None,
                'project_id': None,
                'project_name': None,
                'objective': None,
                'period': None,
                'campaign_id': None
            }]
    else:
        # Set invoice type for all items
        for item in items:
            item['invoice_type'] = invoice_type
    
    return items

def extract_google_ap_comprehensive(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract all Google AP line items with comprehensive pattern matching"""
    
    items = []
    lines = text_content.split('\n')
    
    # Pattern variations for pk|
    pk_patterns = [
        r'pk\|(\d+)\|([^_]+)_pk_([^_]+)_none_([^_]+)_([^_\[]+)(?:_\[ST\]\|)?([A-Z0-9]+)?',
        r'pk[|｜](\d+)[|｜]([^\s]+)',
        r'(pk\s*\|\s*[^\n]+)',
        r'pk\|[^\|]+\|[^\|]+\|[^\|]+\[ST\]\|[A-Z0-9]+'
    ]
    
    # Process line by line
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Try to find pk pattern
        found = False
        for pattern in pk_patterns:
            match = re.search(pattern, line)
            if match:
                found = True
                break
        
        if found or ('pk' in line and ('|' in line or '｜' in line)):
            # Extract full pattern
            pk_pattern = line
            
            # Check if pattern continues on next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'^\]?\|[A-Z0-9]+', next_line):
                    pk_pattern += next_line
            
            # Look for amount
            amount = 0.0
            quantity = 0
            unit = ''
            
            # Search in next few lines for amount
            for j in range(i, min(i + 5, len(lines))):
                check_line = lines[j].strip()
                
                # Pattern: "25297 การคลิก 9,895.90"
                full_match = re.search(r'(\d+)\s+(\S+)\s+([\d,]+\.?\d*)\s*$', check_line)
                if full_match:
                    try:
                        quantity = int(full_match.group(1))
                        unit = full_match.group(2)
                        amount = float(full_match.group(3).replace(',', ''))
                        break
                    except:
                        pass
                
                # Just amount
                amount_match = re.search(r'([\d,]+\.\d{2})\s*$', check_line)
                if amount_match and j > i:
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                        break
                    except:
                        pass
            
            if amount > 0:
                # Parse fields from pattern
                ap_fields = parse_google_ap_pattern(pk_pattern)
                
                item = {
                    **base_fields,
                    'line_number': len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': clean_pattern(pk_pattern),
                    'quantity': quantity,
                    'unit': unit,
                    **ap_fields
                }
                items.append(item)
        
        # Check for credit lines (negative amounts)
        elif 'กิจกรรมที่ไม่ถูกต้อง' in line or 'Invalid activity' in line:
            # Look for negative amount
            for j in range(i + 1, min(i + 5, len(lines))):
                check_line = lines[j].strip()
                
                # Negative amount pattern
                neg_match = re.match(r'^-(\d+\.?\d*)\s*$', check_line)
                if neg_match:
                    try:
                        amount = -float(neg_match.group(1))
                        
                        # Try to extract campaign info from description
                        desc = line
                        if 'pk' in line:
                            pk_match = re.search(r'pk[|｜][^\s,]+', line)
                            if pk_match:
                                ap_fields = parse_google_ap_pattern(pk_match.group(0))
                            else:
                                ap_fields = default_credit_fields()
                        else:
                            ap_fields = default_credit_fields()
                        
                        item = {
                            **base_fields,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': desc[:200],
                            **ap_fields
                        }
                        items.append(item)
                        break
                    except:
                        pass
        
        # Check for fees
        elif 'ค่าธรรมเนียม' in line:
            amount = extract_fee_amount(line)
            if amount > 0:
                fee_type = 'Fee'
                if 'สเปน' in line or 'Spain' in line:
                    fee_type = 'Regulatory Fee - Spain'
                elif 'ฝรั่งเศส' in line or 'France' in line:
                    fee_type = 'Regulatory Fee - France'
                
                item = {
                    **base_fields,
                    'line_number': len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': line.strip(),
                    'agency': None,
                    'project_id': 'Fee',
                    'project_name': fee_type,
                    'objective': None,
                    'period': None,
                    'campaign_id': None
                }
                items.append(item)
        
        i += 1
    
    return items

def extract_google_non_ap(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Google Non-AP invoice"""
    
    # Get total amount
    total = extract_total_amount(text_content)
    
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
        'amount': total,
        'total': total,
        'agency': None,
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': period if period else None,
        'campaign_id': None
    }
    
    return [item]

def parse_google_ap_pattern(pattern: str) -> Dict[str, str]:
    """Parse Google AP pattern with multiple format support"""
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown',
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    # Clean pattern
    pattern = clean_pattern(pattern)
    
    # Try structured parsing first
    # Pattern: pk|70092|Apitown_pk_th-upcountry-projects-apitown-udonthani_none_Traffic_Responsive_[ST]|2100P02
    struct_match = re.match(r'pk[|｜](\d+)[|｜]([^_]+)_pk_([^_]+)_none_([^_]+)_([^_\[]+)(?:_?\[ST\][|｜])?([A-Z0-9]+)?', pattern)
    
    if struct_match:
        result['project_id'] = struct_match.group(1)
        result['project_name'] = struct_match.group(2).replace('-', ' ').title()
        
        # Parse location/details
        details = struct_match.group(3)
        if 'upcountry-projects-apitown' in details:
            location = details.split('-')[-1]
            result['project_name'] = f'Apitown - {location.title()}'
        
        # Objective
        obj = struct_match.group(4)
        if obj == 'Traffic':
            # Check for sub-type
            sub_type = struct_match.group(5)
            if 'Search_Generic' in sub_type:
                result['objective'] = 'Search - Generic'
            elif 'Search_Compet' in sub_type:
                result['objective'] = 'Search - Competitor'
            elif 'Search_Brand' in sub_type:
                result['objective'] = 'Search - Brand'
            else:
                result['objective'] = 'Traffic'
        else:
            result['objective'] = obj
        
        # Campaign ID
        if struct_match.group(6):
            result['campaign_id'] = struct_match.group(6)
    else:
        # Fallback parsing
        parts = re.split(r'[|｜]', pattern)
        
        if len(parts) >= 2:
            # Project ID
            if parts[1].isdigit():
                result['project_id'] = parts[1]
            
            # Parse remaining content
            if len(parts) > 2:
                content = '|'.join(parts[2:])
                
                # Extract project name
                if 'Apitown' in content:
                    result['project_name'] = 'Apitown'
                    if 'udonthani' in content.lower():
                        result['project_name'] = 'Apitown - Udonthani'
                
                # Extract objective
                for obj in ['Traffic', 'Awareness', 'Engagement', 'Conversion']:
                    if obj in content:
                        result['objective'] = obj
                        break
                
                # Extract campaign ID
                id_match = re.search(r'\[ST\][|｜]([A-Z0-9]+)', content)
                if id_match:
                    result['campaign_id'] = id_match.group(1)
    
    return result

def extract_total_amount(text_content: str) -> float:
    """Extract total amount from invoice"""
    
    # Try multiple patterns
    patterns = [
        r'จำนวนเงินรวมที่ต้องชำระในสกุลเงิน\s+THB\s*[:\s]*(-?[฿$]?[\d,]+\.?\d*)',
        r'ยอดรวมในสกุลเงิน\s+THB\s*[:\s]*(-?[฿$]?[\d,]+\.?\d*)',
        r'Total.*THB.*?(-?[\d,]+\.?\d*)',
        r'฿\s*([\d,]+\.\d{2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1)
                amount_str = amount_str.replace('฿', '').replace('$', '').replace(',', '').strip()
                return float(amount_str)
            except:
                pass
    
    return 0.0

def extract_fee_amount(line: str) -> float:
    """Extract fee amount from line"""
    
    amount_match = re.search(r'(\d+\.?\d*)\s*$', line)
    if amount_match:
        try:
            return float(amount_match.group(1))
        except:
            pass
    return 0.0

def clean_pattern(pattern: str) -> str:
    """Clean up pattern for better readability"""
    pattern = re.sub(r'\s+', ' ', pattern.strip())
    pattern = pattern.replace('｜', '|')  # Normalize pipe character
    return pattern

def default_credit_fields() -> dict:
    """Default fields for credit adjustments"""
    return {
        'agency': 'pk',
        'project_id': 'Credit',
        'project_name': 'Credit Adjustment',
        'objective': 'N/A',
        'period': 'N/A',
        'campaign_id': 'CREDIT'
    }

if __name__ == "__main__":
    print("Google Advanced Parser - Ready")