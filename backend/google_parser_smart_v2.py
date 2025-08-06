#!/usr/bin/env python3
"""
Smart Google parser V2 - Extract actual line items like Facebook and TikTok
No lookup tables - pure extraction
"""

import re
from typing import Dict, List, Any, Tuple
import fitz

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice with smart line item extraction"""
    
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
    
    # Clean text from zero-width characters
    text_content = clean_text(text_content)
    
    # Detect invoice type
    invoice_type = detect_invoice_type(text_content)
    
    # Extract line items
    items = extract_line_items(text_content, base_fields, invoice_type)
    
    # Set invoice type
    for item in items:
        item['invoice_type'] = invoice_type
    
    # If no items found, create at least one
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
                'period': extract_period(text_content),
                'campaign_id': None
            }]
    
    return items

def clean_text(text: str) -> str:
    """Clean text from zero-width and special characters"""
    # Remove zero-width characters
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    return text

def detect_invoice_type(text_content: str) -> str:
    """Detect if invoice is AP or Non-AP"""
    
    # Check for AP indicators
    ap_indicators = [
        r'pk\s*[|｜]',  # pk| pattern
        r'การคลิก',     # Thai "clicks"
        r'Click',       # English "clicks"
        r'Campaign',
        r'แคมเปญ',      # Thai "campaign"
        r'Impression',
        r'การแสดงผล',   # Thai "impressions"
        r'Search',
        r'Display',
        r'Traffic'
    ]
    
    ap_score = sum(1 for pattern in ap_indicators if re.search(pattern, text_content, re.IGNORECASE))
    
    # Check for Non-AP indicators
    non_ap_indicators = [
        r'คืนเงิน',              # Refund
        r'[Rr]efund',
        r'[Cc]redit\s+[Nn]ote',
        r'ยอดติดลบ',            # Negative balance
        r'[Nn]egative\s+[Bb]alance'
    ]
    
    non_ap_score = sum(1 for pattern in non_ap_indicators if re.search(pattern, text_content, re.IGNORECASE))
    
    # Check if mostly negative amounts
    amounts = re.findall(r'-?\d{1,3}(?:,\d{3})*\.\d{2}', text_content)
    if amounts:
        negative_count = sum(1 for amt in amounts if amt.startswith('-'))
        if negative_count > len(amounts) * 0.6:
            return 'Non-AP'
    
    # Decision
    if non_ap_score > 0:
        return 'Non-AP'
    elif ap_score >= 2:
        return 'AP'
    else:
        # Default based on content
        return 'AP' if len(text_content.split('\n')) > 300 else 'Non-AP'

def extract_line_items(text_content: str, base_fields: dict, invoice_type: str) -> List[Dict[str, Any]]:
    """Extract line items from invoice"""
    
    items = []
    lines = text_content.split('\n')
    
    # For AP invoices, look for campaign line items
    if invoice_type == 'AP':
        items = extract_ap_line_items(lines, base_fields)
    
    # Also extract credits and fees
    credit_items = extract_credit_items(lines, base_fields, len(items))
    items.extend(credit_items)
    
    fee_items = extract_fee_items(lines, base_fields, len(items))
    items.extend(fee_items)
    
    # If still no items for Non-AP, extract summary
    if not items and invoice_type == 'Non-AP':
        items = extract_non_ap_summary(text_content, base_fields)
    
    return items

def extract_ap_line_items(lines: List[str], base_fields: dict) -> List[Dict[str, Any]]:
    """Extract AP campaign line items"""
    
    items = []
    
    # Pattern for amounts (including decimals)
    amount_pattern = re.compile(r'^(\d{1,3}(?:,\d{3})*\.\d{2})$')
    
    # Pattern for pk| lines (even if fragmented)
    pk_indicators = ['pk', '|', 'Traffic', 'Search', 'Display', 'Campaign']
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this might be a campaign line
        if any(indicator in line for indicator in pk_indicators):
            # Look for amount in nearby lines
            amount = 0
            desc = line
            
            # Collect full description if fragmented
            if len(line) < 10:
                desc_parts = [line]
                j = i + 1
                while j < min(i + 20, len(lines)):
                    next_line = lines[j].strip()
                    if amount_pattern.match(next_line):
                        # Found amount
                        amount = float(next_line.replace(',', ''))
                        desc = ' '.join(desc_parts)
                        break
                    elif len(next_line) > 0:
                        desc_parts.append(next_line)
                    j += 1
            else:
                # Look for amount after description
                for j in range(i + 1, min(i + 10, len(lines))):
                    amt_match = amount_pattern.match(lines[j].strip())
                    if amt_match:
                        amount = float(amt_match.group(1).replace(',', ''))
                        break
            
            if amount > 0:
                ap_fields = parse_ap_fields(desc)
                item = {
                    **base_fields,
                    'line_number': len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': desc[:200],
                    **ap_fields
                }
                items.append(item)
        
        # Also check for standalone amounts with context
        elif amount_pattern.match(line):
            try:
                amount = float(line.replace(',', ''))
                
                # Skip small amounts (< 100) and very large amounts (> 1M)
                if 100 <= amount <= 1000000:
                    # Find description
                    desc = find_description_for_amount(lines, i)
                    
                    # Check if it's a campaign item
                    if any(indicator in desc for indicator in ['Campaign', 'การคลิก', 'Click', 'Impression']):
                        ap_fields = parse_ap_fields(desc)
                        item = {
                            **base_fields,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': desc[:200],
                            **ap_fields
                        }
                        items.append(item)
            except:
                pass
        
        i += 1
    
    return items

def extract_credit_items(lines: List[str], base_fields: dict, start_num: int) -> List[Dict[str, Any]]:
    """Extract credit/refund items"""
    
    items = []
    
    # Pattern for negative amounts
    neg_amount_pattern = re.compile(r'^(-\d{1,3}(?:,\d{3})*\.?\d*)$')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check for credit keywords
        if any(keyword in line for keyword in ['กิจกรรมที่ไม่ถูกต้อง', 'Invalid activity', 'Credit', 'เครดิต']):
            # Look for amount
            for j in range(max(0, i - 2), min(len(lines), i + 5)):
                amt_match = neg_amount_pattern.match(lines[j].strip())
                if amt_match:
                    amount = float(amt_match.group(1).replace(',', ''))
                    item = {
                        **base_fields,
                        'line_number': start_num + len(items) + 1,
                        'amount': amount,
                        'total': amount,
                        'description': line[:200],
                        'agency': 'pk',
                        'project_id': 'Credit',
                        'project_name': 'Credit Adjustment',
                        'objective': 'N/A',
                        'period': 'N/A',
                        'campaign_id': 'CREDIT'
                    }
                    items.append(item)
                    break
        
        # Also check for standalone negative amounts
        elif neg_amount_pattern.match(line):
            amount = float(line.replace(',', ''))
            desc = find_description_for_amount(lines, i)
            
            item = {
                **base_fields,
                'line_number': start_num + len(items) + 1,
                'amount': amount,
                'total': amount,
                'description': desc[:200] if desc else 'Credit adjustment',
                'agency': 'pk',
                'project_id': 'Credit',
                'project_name': 'Credit Adjustment',
                'objective': 'N/A',
                'period': 'N/A',
                'campaign_id': 'CREDIT'
            }
            items.append(item)
    
    return items

def extract_fee_items(lines: List[str], base_fields: dict, start_num: int) -> List[Dict[str, Any]]:
    """Extract fee items"""
    
    items = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Check for fee keywords
        if 'ค่าธรรมเนียม' in line or 'fee' in line.lower():
            # Extract amount from same line
            amt_match = re.search(r'(\d+\.\d{2})', line)
            if amt_match:
                amount = float(amt_match.group(1))
                
                # Fees are typically small amounts
                if 0 < amount < 100:
                    fee_type = 'Regulatory Fee'
                    if 'สเปน' in line or 'Spain' in line:
                        fee_type = 'Regulatory Fee - Spain'
                    elif 'ฝรั่งเศส' in line or 'France' in line:
                        fee_type = 'Regulatory Fee - France'
                    
                    item = {
                        **base_fields,
                        'line_number': start_num + len(items) + 1,
                        'amount': amount,
                        'total': amount,
                        'description': line[:200],
                        'agency': None,
                        'project_id': 'Fee',
                        'project_name': fee_type,
                        'objective': None,
                        'period': None,
                        'campaign_id': None
                    }
                    items.append(item)
    
    return items

def extract_non_ap_summary(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Non-AP summary"""
    
    total = extract_total_amount(text_content)
    
    # Extract account info
    account_match = re.search(r'บัญชี:\s*([^\n]+)', text_content)
    account_name = account_match.group(1).strip() if account_match else 'Google Ads'
    
    # Extract period
    period = extract_period(text_content)
    
    desc = f'{account_name}'
    if period:
        desc += f' ({period})'
    
    item = {
        **base_fields,
        'line_number': 1,
        'description': desc,
        'amount': total,
        'total': total,
        'agency': None,
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': period,
        'campaign_id': None
    }
    
    return [item]

def find_description_for_amount(lines: List[str], amount_idx: int) -> str:
    """Find description for an amount"""
    
    # Look backwards
    for i in range(amount_idx - 1, max(0, amount_idx - 10), -1):
        line = lines[i].strip()
        if len(line) > 15 and not re.match(r'^[\d,.-]+$', line):
            return line
    
    # Look forward
    for i in range(amount_idx + 1, min(len(lines), amount_idx + 5)):
        line = lines[i].strip()
        if len(line) > 15 and not re.match(r'^[\d,.-]+$', line):
            return line
    
    return "Google Ads Campaign"

def parse_ap_fields(description: str) -> Dict[str, str]:
    """Parse AP fields from description"""
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown',
        'period': 'Current',
        'campaign_id': 'Unknown'
    }
    
    desc_lower = description.lower()
    
    # Extract project ID
    id_match = re.search(r'pk[|｜]\s*(\d+)', description)
    if id_match:
        result['project_id'] = id_match.group(1)
    elif re.search(r'\b(\d{5})\b', description):
        result['project_id'] = re.search(r'\b(\d{5})\b', description).group(1)
    
    # Extract project name
    if 'apitown' in desc_lower:
        result['project_name'] = 'Apitown'
        if 'udonthani' in desc_lower:
            result['project_name'] = 'Apitown - Udonthani'
        elif 'phitsanulok' in desc_lower:
            result['project_name'] = 'Apitown - Phitsanulok'
    elif 'sdh' in desc_lower or 'single' in desc_lower:
        result['project_name'] = 'Single Detached House'
    elif 'townhome' in desc_lower or 'th_' in desc_lower:
        result['project_name'] = 'Townhome'
    elif 'online' in desc_lower:
        result['project_name'] = 'Online Marketing'
    
    # Extract objective
    objectives = {
        'traffic': 'Traffic',
        'awareness': 'Awareness',
        'conversion': 'Conversion',
        'engagement': 'Engagement',
        'search': 'Search',
        'display': 'Display',
        'responsive': 'Responsive',
        'lead': 'Lead Generation'
    }
    
    for key, value in objectives.items():
        if key in desc_lower:
            result['objective'] = value
            # Add sub-type if exists
            if value == 'Search':
                if 'generic' in desc_lower:
                    result['objective'] = 'Search - Generic'
                elif 'brand' in desc_lower:
                    result['objective'] = 'Search - Brand'
                elif 'compet' in desc_lower:
                    result['objective'] = 'Search - Competitor'
            break
    
    # Extract campaign ID
    camp_patterns = [
        r'\[ST\][|｜]([A-Z0-9]+)',
        r'[|｜]([0-9]{4}[A-Z][0-9]{2})(?:\s|$)',
        r'_([A-Z0-9]{7})(?:\s|$)'
    ]
    
    for pattern in camp_patterns:
        match = re.search(pattern, description)
        if match:
            result['campaign_id'] = match.group(1)
            break
    
    return result

def extract_total_amount(text_content: str) -> float:
    """Extract total amount from invoice"""
    
    patterns = [
        r'จำนวนเงินรวมที่ต้องชำระในสกุลเงิน\s+THB\s*[:\s]*(-?[฿$]?[\d,]+\.?\d*)',
        r'ยอดรวมในสกุลเงิน\s+THB\s*[:\s]*(-?[฿$]?[\d,]+\.?\d*)',
        r'Total\s+amount\s+due.*?(-?[\d,]+\.\d{2})',
        r'฿\s*(-?[\d,]+\.\d{2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                amount_str = match.group(1)
                amount_str = amount_str.replace('฿', '').replace('$', '').replace(',', '').strip()
                return float(amount_str)
            except:
                pass
    
    return 0.0

def extract_period(text_content: str) -> str:
    """Extract billing period"""
    
    period_match = re.search(r'(\d{1,2}\s+\S+\s+\d{4})\s*-\s*(\d{1,2}\s+\S+\s+\d{4})', text_content)
    if period_match:
        return f"{period_match.group(1)} - {period_match.group(2)}"
    
    return None

if __name__ == "__main__":
    print("Google Smart Parser V2 - Ready")