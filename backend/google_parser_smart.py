#!/usr/bin/env python3
"""
Smart Google parser that handles character fragmentation intelligently
No hardcoding required - works with all Google invoices
"""

import re
from typing import Dict, List, Any
import fitz

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Smart Google parser that handles both AP and Non-AP intelligently"""
    
    # Extract invoice number
    invoice_number = filename.replace('.pdf', '') if filename else 'Unknown'
    inv_match = re.search(r'หมายเลขใบแจ้งหนี้:\s*(\d+)', text_content)
    if not inv_match:
        inv_match = re.search(r'Invoice number:\s*(\d+)', text_content)
        if not inv_match:
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
    
    # First, try to reconstruct fragmented text
    reconstructed_text = reconstruct_fragmented_text(text_content)
    
    # Classify invoice type intelligently
    invoice_type = classify_google_invoice(reconstructed_text, text_content)
    
    if invoice_type == "AP":
        # Extract AP items
        items = extract_google_ap_smart(reconstructed_text, text_content, base_fields)
    else:
        # Extract Non-AP
        items = extract_google_non_ap(text_content, base_fields)
    
    # Set invoice type for all items
    for item in items:
        item['invoice_type'] = invoice_type
    
    # If no items, create at least one
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
    
    return items

def reconstruct_fragmented_text(text_content: str) -> str:
    """Reconstruct fragmented character patterns intelligently"""
    
    lines = text_content.split('\n')
    reconstructed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect potential fragmentation: single character lines
        if len(line) <= 3 and line in 'pk|0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_-[]':
            # Start collecting fragmented pattern
            collected = []
            j = i
            
            # Look ahead to collect pattern
            while j < len(lines) and j < i + 200:
                current = lines[j].strip()
                
                # Stop conditions
                if not current:  # Empty line
                    j += 1
                    continue
                elif re.match(r'^\d{1,3}(?:,\d{3})*\.\d{2}$', current):  # Amount
                    if collected:
                        reconstructed_lines.append(''.join(collected))
                    reconstructed_lines.append(current)
                    j += 1
                    break
                elif len(current) > 20 and ' ' in current:  # Long text
                    if collected:
                        reconstructed_lines.append(''.join(collected))
                    reconstructed_lines.append(current)
                    j += 1
                    break
                elif 'หน้า' in current and 'จาก' in current:  # Page marker
                    break
                elif 'การคลิก' in current or 'Click' in current:  # Unit
                    if collected:
                        reconstructed_lines.append(''.join(collected))
                    j += 1
                    break
                
                # Collect if looks like part of pattern
                if len(current) <= 10:
                    collected.append(current)
                else:
                    if collected:
                        reconstructed_lines.append(''.join(collected))
                    reconstructed_lines.append(current)
                    j += 1
                    break
                
                j += 1
            
            # Handle remaining collected
            if j >= i + 200 and collected:
                reconstructed_lines.append(''.join(collected))
            
            i = j
        else:
            reconstructed_lines.append(line)
            i += 1
    
    return '\n'.join(reconstructed_lines)

def classify_google_invoice(reconstructed_text: str, original_text: str) -> str:
    """Intelligently classify Google invoice as AP or Non-AP"""
    
    # Check for pk| patterns
    has_pk_reconstructed = bool(re.search(r'pk\|', reconstructed_text))
    
    # Check for other AP indicators
    ap_indicators = [
        'pk|', 'Apitown', 'SDH_pk', 'OnlineMKT_pk', 'upcountry',
        'Traffic', 'Awareness', 'Conversion', 'Engagement',
        '[ST]', 'การคลิก', 'Click'
    ]
    
    ap_score = sum(1 for indicator in ap_indicators if indicator in reconstructed_text or indicator in original_text)
    
    # Check for Non-AP indicators
    non_ap_indicators = [
        'กิจกรรมที่ไม่ถูกต้อง', 'Invalid activity', 
        'Refund', 'Credit', 'Adjustment',
        'เครดิต', 'คืนเงิน'
    ]
    
    non_ap_score = sum(1 for indicator in non_ap_indicators if indicator in original_text)
    
    # Check if all amounts are negative (refund invoice)
    amounts = re.findall(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', original_text)
    if amounts:
        negative_count = sum(1 for amt in amounts if amt.startswith('-'))
        if negative_count > len(amounts) * 0.8:  # 80% negative = refund
            return "Non-AP"
    
    # Classification logic
    if has_pk_reconstructed or ap_score >= 3:
        return "AP"
    elif non_ap_score >= 2:
        return "Non-AP"
    else:
        # Check page count and content length
        line_count = len(original_text.split('\n'))
        if line_count > 500:  # Long invoices usually AP
            return "AP"
        else:
            return "Non-AP"

def extract_google_ap_smart(reconstructed_text: str, original_text: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract AP items using smart pattern recognition"""
    
    items = []
    lines = reconstructed_text.split('\n')
    
    # Pattern variations for pk|
    pk_patterns = [
        # Standard pattern
        r'(pk\|[^|]+\|[^|]+\|[^|]+\[ST\]\|[A-Z0-9]+)',
        # Pattern with spaces
        r'(pk\s*\|\s*[^|]+\s*\|\s*[^|]+)',
        # Simplified pattern
        r'(pk\|[\w\s_-]+)'
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Try each pk pattern
        found_pk = False
        for pattern in pk_patterns:
            match = re.search(pattern, line)
            if match:
                found_pk = True
                pk_pattern = match.group(1)
                break
        
        if found_pk or 'pk|' in line:
            # Extract the full pattern
            if not found_pk:
                pk_pattern = line
            
            # Look for associated amount
            amount = 0.0
            quantity = 0
            unit = ''
            
            # Search nearby lines for amount
            for j in range(i-2, min(i+10, len(lines))):
                if j < 0:
                    continue
                check_line = lines[j].strip()
                
                # Pattern: quantity unit amount
                full_match = re.match(r'^(\d{1,3}(?:,\d{3})*)\s+([\u0E00-\u0E7F\w]+)\s+(\d{1,3}(?:,\d{3})*\.\d{2})$', check_line)
                if full_match:
                    try:
                        quantity = int(full_match.group(1).replace(',', ''))
                        unit = full_match.group(2)
                        amount = float(full_match.group(3).replace(',', ''))
                        break
                    except:
                        pass
                
                # Just amount
                amt_match = re.match(r'^(\d{1,3}(?:,\d{3})*\.\d{2})$', check_line)
                if amt_match:
                    try:
                        amount = float(amt_match.group(1).replace(',', ''))
                        break
                    except:
                        pass
            
            if amount > 0:
                # Parse AP fields
                ap_fields = parse_google_ap_fields_smart(pk_pattern)
                
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
        
        # Check for credits (negative amounts)
        elif re.match(r'^-\d+\.?\d*$', line):
            try:
                amount = float(line)
                
                # Find description
                desc = 'Credit adjustment'
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if 'กิจกรรม' in prev_line or len(prev_line) > 10:
                        desc = prev_line
                
                item = {
                    **base_fields,
                    'line_number': len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': desc,
                    'agency': 'pk',
                    'project_id': 'Credit',
                    'project_name': 'Credit Adjustment',
                    'objective': 'N/A',
                    'period': 'N/A',
                    'campaign_id': 'CREDIT'
                }
                items.append(item)
            except:
                pass
        
        # Check for fees
        elif 'ค่าธรรมเนียม' in line:
            amt_match = re.search(r'(\d+\.\d{2})$', line)
            if amt_match:
                try:
                    amount = float(amt_match.group(1))
                    if 0 < amount < 10:  # Fees are small
                        fee_type = 'Regulatory Fee'
                        if 'สเปน' in line:
                            fee_type = 'Regulatory Fee - Spain'
                        elif 'ฝรั่งเศส' in line:
                            fee_type = 'Regulatory Fee - France'
                        
                        item = {
                            **base_fields,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': line,
                            'agency': None,
                            'project_id': 'Fee',
                            'project_name': fee_type,
                            'objective': None,
                            'period': None,
                            'campaign_id': None
                        }
                        items.append(item)
                except:
                    pass
        
        i += 1
    
    return items

def parse_google_ap_fields_smart(pattern: str) -> Dict[str, str]:
    """Smart parsing of AP fields from pattern"""
    
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
    
    # Extract project ID (numbers after pk|)
    id_match = re.search(r'pk\|(\d+)\|', pattern)
    if id_match:
        result['project_id'] = id_match.group(1)
    
    # Extract project name
    project_names = {
        'apitown': 'Apitown',
        'sdh': 'Single Detached House',
        'th': 'Townhome',
        'onlinemkt': 'Online Marketing',
        'centro': 'Centro',
        'upcountry': 'Upcountry Projects'
    }
    
    pattern_lower = pattern.lower()
    for key, name in project_names.items():
        if key in pattern_lower:
            result['project_name'] = name
            # Add location if found
            if 'udonthani' in pattern_lower:
                result['project_name'] += ' - Udonthani'
            elif 'bangkok' in pattern_lower:
                result['project_name'] += ' - Bangkok'
            break
    
    # Extract objective
    objectives = {
        'traffic': 'Traffic',
        'awareness': 'Awareness',
        'conversion': 'Conversion',
        'engagement': 'Engagement',
        'leadad': 'Lead Generation',
        'search_generic': 'Search - Generic',
        'search_compet': 'Search - Competitor',
        'search_brand': 'Search - Brand',
        'responsive': 'Display - Responsive'
    }
    
    for key, obj in objectives.items():
        if key in pattern_lower:
            result['objective'] = obj
            break
    
    # Extract campaign ID
    campaign_patterns = [
        r'\[ST\]\|([A-Z0-9]+)',
        r'\|([0-9]{4}[A-Z][0-9]{2})(?:\s|$)',
        r'_([A-Z0-9]{7})(?:\s|$)'
    ]
    
    for camp_pattern in campaign_patterns:
        camp_match = re.search(camp_pattern, pattern)
        if camp_match:
            result['campaign_id'] = camp_match.group(1)
            break
    
    return result

def extract_google_non_ap(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Non-AP invoice"""
    
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

def extract_total_amount(text_content: str) -> float:
    """Extract total amount from invoice"""
    
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

def clean_pattern(pattern: str) -> str:
    """Clean pattern for readability"""
    # Remove extra spaces
    pattern = re.sub(r'\s+', ' ', pattern)
    # Remove zero-width characters
    pattern = pattern.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    return pattern.strip()

if __name__ == "__main__":
    print("Google Smart Parser - Ready")