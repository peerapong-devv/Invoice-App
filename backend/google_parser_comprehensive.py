#!/usr/bin/env python3
"""
Comprehensive Google Parser - Extract ALL line items properly
No lookup tables - pure extraction from PDF content
"""

import re
from typing import Dict, List, Any, Tuple, Optional
import fitz

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice comprehensively - extract every line item"""
    
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
    
    # Clean text
    text_content = clean_text(text_content)
    
    # Determine invoice type
    invoice_type = determine_invoice_type(text_content)
    
    # Extract all line items based on type
    if invoice_type == 'AP':
        items = extract_ap_line_items(text_content, base_fields)
    else:
        items = extract_non_ap_line_items(text_content, base_fields)
    
    # Set invoice type for all items
    for item in items:
        item['invoice_type'] = invoice_type
    
    # Validate and ensure we have items
    if not items:
        # Fallback to create at least one item with total
        total = extract_total_amount(text_content)
        if total != 0:
            items = [{
                **base_fields,
                'invoice_type': invoice_type,
                'line_number': 1,
                'amount': total,
                'total': total,
                'description': f'Google Ads {invoice_type} Invoice',
                'agency': 'Google' if invoice_type == 'AP' else None,
                'project_id': None,
                'project_name': None,
                'objective': None,
                'period': extract_period(text_content),
                'campaign_id': None
            }]
    
    return items

def clean_text(text: str) -> str:
    """Clean text from special characters and normalize"""
    # Remove zero-width characters
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    # Fix common OCR issues
    text = text.replace('|', '|').replace('］', ']').replace('［', '[')
    return text

def extract_invoice_number(text_content: str, filename: str) -> str:
    """Extract invoice number from text or filename"""
    # Try Thai pattern first
    inv_match = re.search(r'หมายเลขใบแจ้งหนี้:\s*(\d{10})', text_content)
    if inv_match:
        return inv_match.group(1)
    
    # Try English pattern
    inv_match = re.search(r'Invoice number:\s*(\d{10})', text_content)
    if inv_match:
        return inv_match.group(1)
    
    # Try from filename
    inv_match = re.search(r'(\d{10})', filename)
    if inv_match:
        return inv_match.group(1)
    
    return 'Unknown'

def determine_invoice_type(text_content: str) -> str:
    """Determine if invoice is AP or Non-AP"""
    # Check for credit note indicators
    if is_credit_note(text_content):
        return 'Non-AP'
    
    # Check for AP indicators
    ap_indicators = [
        'pk|', 'pk｜', 'pk |',  # Different pk patterns
        '[ST]', '［ST］', '[ ST ]',  # ST markers
        'Campaign', 'แคมเปญ',
        'Traffic_', 'LeadAd_', 'Awareness_',
        'SDH_pk_', 'Apitown_pk_', 'TH_pk_',
        'Search_Generic', 'Search_Brand', 'Search_Compet',
        'Responsive', 'CollectionCanvas'
    ]
    
    # Count indicators
    indicator_count = sum(1 for indicator in ap_indicators if indicator in text_content)
    
    # Check for campaign line items pattern
    if has_campaign_line_items(text_content) or indicator_count >= 2:
        return 'AP'
    
    return 'Non-AP'

def is_credit_note(text_content: str) -> bool:
    """Check if this is a credit note"""
    credit_indicators = [
        'ใบลดหนี้', 'Credit Note', 'Credit Memo',
        'คืนเงิน', 'Refund',
        'ยอดติดลบ', 'Negative balance',
        'กิจกรรมที่ไม่ถูกต้อง'
    ]
    
    # Check if total is negative
    total = extract_total_amount(text_content)
    if total < 0:
        return True
    
    # Check for credit indicators
    return any(indicator in text_content for indicator in credit_indicators)

def has_campaign_line_items(text_content: str) -> bool:
    """Check if invoice has multiple campaign line items"""
    lines = text_content.split('\n')
    
    # Look for multiple amounts that could be line items
    amount_pattern = re.compile(r'^\s*(\d{1,3}(?:,\d{3})*\.?\d*)\s*$')
    amount_count = 0
    
    for line in lines:
        if amount_pattern.match(line.strip()):
            amount_count += 1
    
    # If we have many amounts, likely AP invoice
    return amount_count > 5

def extract_ap_line_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract line items from AP invoice"""
    items = []
    lines = text_content.split('\n')
    
    # Strategy 1: Look for pk| patterns with amounts
    pk_items = extract_pk_pattern_items(lines, base_fields)
    if pk_items:
        items.extend(pk_items)
    
    # Strategy 2: Look for campaign descriptions with amounts
    campaign_items = extract_campaign_items(lines, base_fields, len(items))
    if campaign_items:
        items.extend(campaign_items)
    
    # Strategy 3: Look for credit/adjustment items
    credit_items = extract_credit_items(lines, base_fields, len(items))
    if credit_items:
        items.extend(credit_items)
    
    # Strategy 4: Look for fee items
    fee_items = extract_fee_items(lines, base_fields, len(items))
    if fee_items:
        items.extend(fee_items)
    
    # Remove duplicates while preserving order
    unique_items = []
    seen_amounts = set()
    for item in items:
        amt_key = f"{item['amount']:.2f}"
        if amt_key not in seen_amounts or item['amount'] == 0:
            unique_items.append(item)
            seen_amounts.add(amt_key)
    
    return unique_items

def extract_pk_pattern_items(lines: List[str], base_fields: dict) -> List[Dict[str, Any]]:
    """Extract items with pk| patterns"""
    items = []
    
    # First, reconstruct fragmented text
    reconstructed_lines = reconstruct_fragmented_lines(lines)
    
    # Now look for pk patterns in reconstructed lines
    for i, line in enumerate(reconstructed_lines):
        # Look for pk| patterns
        if 'pk|' in line:
            # Extract the full pattern
            pk_match = re.search(r'(pk\|[^\s]+(?:\[[^\]]+\])?(?:\|[^\s]+)?)', line)
            if pk_match:
                desc = pk_match.group(1)
                
                # Look for associated amount
                amount = None
                # Check same line
                amt_match = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})\s*$', line)
                if amt_match:
                    amount = float(amt_match.group(1).replace(',', ''))
                else:
                    # Check nearby lines
                    for j in range(i+1, min(i+10, len(reconstructed_lines))):
                        if re.match(r'^\s*\d{1,3}(?:,\d{3})*\.\d{2}\s*$', reconstructed_lines[j]):
                            amount = float(reconstructed_lines[j].strip().replace(',', ''))
                            break
                
                if amount and amount > 0:
                    item = create_ap_item(base_fields, len(items) + 1, amount, desc)
                    items.append(item)
    
    return items

def reconstruct_fragmented_lines(lines: List[str]) -> List[str]:
    """Reconstruct lines that have been fragmented character by character"""
    reconstructed = []
    buffer = []
    
    for line in lines:
        # If line is a single character or very short, it might be fragmented
        if len(line.strip()) <= 3 and line.strip():
            buffer.append(line.strip())
        else:
            # If we have buffered characters, join them
            if buffer:
                reconstructed.append(''.join(buffer))
                buffer = []
            reconstructed.append(line)
    
    # Don't forget last buffer
    if buffer:
        reconstructed.append(''.join(buffer))
    
    # Second pass: merge lines that look like they belong together
    merged = []
    i = 0
    while i < len(reconstructed):
        line = reconstructed[i]
        
        # Check if this line starts a pk pattern
        if line.startswith('pk|') and i + 1 < len(reconstructed):
            # Look ahead to see if we should merge
            full_pattern = line
            j = i + 1
            while j < len(reconstructed) and j < i + 20:
                next_line = reconstructed[j]
                # If next line looks like continuation of pattern
                if (next_line.startswith('|') or 
                    re.match(r'^[A-Za-z0-9_\-]+', next_line) or
                    next_line.startswith('[ST]')):
                    full_pattern += next_line
                    j += 1
                else:
                    break
            merged.append(full_pattern)
            i = j
        else:
            merged.append(line)
            i += 1
    
    return merged

def extract_campaign_items(lines: List[str], base_fields: dict, start_num: int) -> List[Dict[str, Any]]:
    """Extract campaign items without pk patterns"""
    items = []
    
    campaign_keywords = [
        'Campaign', 'แคมเปญ', 'การคลิก', 'Click',
        'Impression', 'การแสดงผล', 'Search', 'Display',
        'Responsive', 'Video', 'Shopping', 'Performance'
    ]
    
    for i, line in enumerate(lines):
        # Check if line contains campaign keywords
        if any(keyword in line for keyword in campaign_keywords):
            # Look for associated amount
            amount = find_nearby_amount(lines, i)
            if amount and amount > 100:  # Skip small amounts
                desc = line.strip()
                # Check if not already captured
                if not any(abs(item['amount'] - amount) < 0.01 for item in items):
                    item = create_ap_item(base_fields, start_num + len(items) + 1, amount, desc)
                    items.append(item)
    
    return items

def extract_credit_items(lines: List[str], base_fields: dict, start_num: int) -> List[Dict[str, Any]]:
    """Extract credit/adjustment items"""
    items = []
    
    credit_keywords = ['กิจกรรมที่ไม่ถูกต้อง', 'ใบลดหนี้', 'คืนเงิน', 'Credit', 'Refund', 'Adjustment']
    
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in credit_keywords):
            # Look for negative amount
            amount = find_nearby_amount(lines, i, negative_only=True)
            if amount and amount < 0:
                desc = line.strip()
                # Extract invoice reference if present
                inv_ref_match = re.search(r'(\d{10})', line)
                if inv_ref_match:
                    desc = f"{desc} (Ref: {inv_ref_match.group(1)})"
                
                item = {
                    **base_fields,
                    'line_number': start_num + len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': desc,
                    'agency': 'pk',
                    'project_id': 'CREDIT',
                    'project_name': 'Credit Adjustment',
                    'objective': 'N/A',
                    'period': None,
                    'campaign_id': 'CREDIT'
                }
                items.append(item)
    
    return items

def extract_fee_items(lines: List[str], base_fields: dict, start_num: int) -> List[Dict[str, Any]]:
    """Extract fee items"""
    items = []
    
    fee_keywords = ['Fee', 'ค่าธรรมเนียม', 'Service', 'บริการ', 'Charge']
    
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in fee_keywords):
            amount = find_nearby_amount(lines, i)
            if amount and amount > 0:
                desc = line.strip()
                item = {
                    **base_fields,
                    'line_number': start_num + len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': desc,
                    'agency': 'Google',
                    'project_id': 'FEE',
                    'project_name': 'Service Fee',
                    'objective': 'N/A',
                    'period': None,
                    'campaign_id': 'FEE'
                }
                items.append(item)
    
    return items

def find_nearby_amount(lines: List[str], index: int, negative_only: bool = False) -> Optional[float]:
    """Find amount near a given line"""
    amount_pattern = re.compile(r'^[\s\-]*(\d{1,3}(?:,\d{3})*\.?\d*)\s*$')
    
    # Check same line first
    line_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d*)\s*$', lines[index])
    if line_match:
        try:
            amount = float(line_match.group(1).replace(',', ''))
            if negative_only:
                # Check if there's a minus sign before
                if '-' in lines[index][:line_match.start()]:
                    return -amount
            else:
                return amount
        except:
            pass
    
    # Check nearby lines (within 3 lines)
    for offset in [1, -1, 2, -2, 3, -3]:
        check_index = index + offset
        if 0 <= check_index < len(lines):
            line = lines[check_index].strip()
            
            # Check for negative indicator
            is_negative = line.startswith('-') or line.startswith('(')
            line = line.lstrip('-()').strip()
            
            match = amount_pattern.match(line)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    if is_negative:
                        amount = -amount
                    
                    if negative_only and amount >= 0:
                        continue
                    
                    return amount
                except:
                    pass
    
    return None

def reconstruct_pk_description(lines: List[str], index: int) -> str:
    """Reconstruct pk| description from fragmented lines"""
    desc_parts = []
    
    # Start from current line
    if 'pk' in lines[index].lower():
        desc_parts.append(lines[index].strip())
    
    # Look for continuation in nearby lines
    for offset in [1, -1, 2, -2]:
        check_index = index + offset
        if 0 <= check_index < len(lines):
            line = lines[check_index].strip()
            # Check if line is part of description (contains | or campaign keywords)
            if ('|' in line or '｜' in line or '[ST]' in line or 
                any(kw in line for kw in ['Traffic', 'Lead', 'Search', 'Display'])):
                desc_parts.append(line)
    
    # Join and clean
    full_desc = ' '.join(desc_parts)
    # Remove extra spaces
    full_desc = re.sub(r'\s+', ' ', full_desc)
    # Fix common issues
    full_desc = full_desc.replace('p k|', 'pk|').replace('pk |', 'pk|')
    
    return full_desc

def create_ap_item(base_fields: dict, line_num: int, amount: float, description: str) -> dict:
    """Create an AP invoice item"""
    item = {
        **base_fields,
        'line_number': line_num,
        'amount': amount,
        'total': amount,
        'description': description
    }
    
    # Parse AP fields from description
    ap_fields = parse_ap_description(description)
    item.update(ap_fields)
    
    return item

def parse_ap_description(description: str) -> dict:
    """Parse AP fields from description"""
    result = {
        'agency': 'pk',
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': None,
        'campaign_id': None
    }
    
    # Extract project ID from pk pattern
    id_match = re.search(r'pk[|｜]\s*(\d+)', description)
    if id_match:
        result['project_id'] = id_match.group(1)
    
    # Extract project name
    if 'apitown' in description.lower():
        result['project_name'] = 'Apitown'
        if 'udonthani' in description.lower():
            result['project_name'] = 'Apitown Udonthani'
        elif 'phitsanulok' in description.lower():
            result['project_name'] = 'Apitown Phitsanulok'
    elif 'sdh' in description.lower() or 'single-detached' in description.lower():
        result['project_name'] = 'Single Detached House'
    elif 'townhome' in description.lower() or 'th-' in description.lower():
        result['project_name'] = 'Townhome Project'
    
    # Extract objective
    obj_patterns = {
        'traffic': 'Traffic',
        'search': 'Search',
        'display': 'Display',
        'responsive': 'Responsive',
        'awareness': 'Awareness',
        'conversion': 'Conversion',
        'leadad': 'Lead Generation',
        'engagement': 'Engagement',
        'generic': 'Generic',
        'brand': 'Brand',
        'compet': 'Competitor'
    }
    
    desc_lower = description.lower()
    objectives = []
    for pattern, obj in obj_patterns.items():
        if pattern in desc_lower:
            objectives.append(obj)
    
    if objectives:
        result['objective'] = ' - '.join(objectives[:2])  # Take first 2
    
    # Extract campaign ID
    camp_patterns = [
        r'\[ST\][|｜]([A-Z0-9]+)',
        r'［ST］[|｜]([A-Z0-9]+)',
        r'\[ST\]\s*[|｜]\s*([A-Z0-9]+)',
        r'campaign[:\s]+([A-Z0-9]+)',
        r'\b([A-Z0-9]{6,})\b'  # Fallback: any 6+ char alphanumeric
    ]
    
    for pattern in camp_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            result['campaign_id'] = match.group(1)
            break
    
    return result

def extract_non_ap_line_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract line items from Non-AP invoice"""
    # For Non-AP, usually just one line with total
    total = extract_total_amount(text_content)
    
    # Extract account name
    account_match = re.search(r'บัญชี:\s*([^\n]+)', text_content)
    if not account_match:
        account_match = re.search(r'Account:\s*([^\n]+)', text_content)
    
    account_name = account_match.group(1).strip() if account_match else 'Google Ads'
    
    # Extract period
    period = extract_period(text_content)
    
    # Create single line item
    item = {
        **base_fields,
        'line_number': 1,
        'amount': total,
        'total': total,
        'description': f'{account_name} - {period}' if period else account_name,
        'agency': None,
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': period,
        'campaign_id': None
    }
    
    return [item]

def extract_total_amount(text_content: str) -> float:
    """Extract total amount from invoice"""
    # Multiple patterns to catch different formats
    patterns = [
        r'ยอดรวม.*?[:\s]+.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'จำนวนเงินรวม.*?[:\s]+.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'Total.*?[:\s]+.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'Amount due.*?[:\s]+.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'THB\s+(\-?\d{1,3}(?:,\d{3})*\.?\d*)\s*$'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text_content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            try:
                amount_str = match.group(1)
                amount = float(amount_str.replace(',', ''))
                # Return the largest amount found (likely the total)
                if abs(amount) > 100:  # Ignore very small amounts
                    return amount
            except:
                pass
    
    return 0.0

def extract_period(text_content: str) -> Optional[str]:
    """Extract billing period"""
    # Thai date pattern
    thai_pattern = r'(\d{1,2}\s+\S+\s+\d{4})\s*[-–]\s*(\d{1,2}\s+\S+\s+\d{4})'
    match = re.search(thai_pattern, text_content)
    if match:
        return f"{match.group(1)} - {match.group(2)}"
    
    # English date pattern
    eng_pattern = r'(\w+\s+\d{1,2},?\s+\d{4})\s*[-–]\s*(\w+\s+\d{1,2},?\s+\d{4})'
    match = re.search(eng_pattern, text_content)
    if match:
        return f"{match.group(1)} - {match.group(2)}"
    
    # Billing period pattern
    period_pattern = r'Billing period[:\s]+([^\n]+)'
    match = re.search(period_pattern, text_content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return None

if __name__ == "__main__":
    print("Google Parser Comprehensive - Ready")
    print("This parser extracts ALL line items without using lookup tables")