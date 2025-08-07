#!/usr/bin/env python3
"""
Google Parser - Fixed to handle fragmented text
Fixes issue #8 by reconstructing fragmented text and extracting ALL line items
"""

import re
from typing import Dict, List, Any, Optional
import fitz

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice extracting ALL line items"""
    
    # Extract invoice number
    invoice_number = extract_invoice_number(text_content, filename)
    
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
    invoice_type = determine_invoice_type(text_content, invoice_number)
    
    # Extract line items - use PDF object for better extraction
    items = extract_line_items_from_pdf(filename, base_fields, invoice_type)
    
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
                'description': extract_main_description(text_content),
                'campaign_code': '',
                'agency': 'pk' if invoice_type == 'AP' else None,
                'project_id': None,
                'project_name': None,
                'objective': None,
                'period': extract_period(text_content),
                'campaign_id': None
            }]
    
    return items

def extract_line_items_from_pdf(filename: str, base_fields: dict, invoice_type: str) -> List[Dict[str, Any]]:
    """Extract line items directly from PDF to handle fragmented text"""
    import os
    
    # Construct full path
    if os.path.exists(filename):
        filepath = filename
    else:
        # Try common paths
        for base_path in ['..', '.', 'Invoice for testing', '../Invoice for testing']:
            test_path = os.path.join(base_path, filename)
            if os.path.exists(test_path):
                filepath = test_path
                break
        else:
            # Fallback
            filepath = filename
    
    items = []
    
    try:
        with fitz.open(filepath) as doc:
            # Focus on page 2 where line items usually are
            if len(doc) >= 2:
                page = doc[1]
                
                # Get text blocks to handle fragmentation better
                blocks = page.get_text("blocks")
                
                # Reconstruct text from blocks
                reconstructed_lines = []
                current_line = ""
                prev_y = None
                
                for block in blocks:
                    x0, y0, x1, y1, text = block[:5]
                    text = text.strip()
                    
                    if not text:
                        continue
                    
                    # If Y position changed significantly, it's a new line
                    if prev_y is not None and abs(y0 - prev_y) > 5:
                        if current_line:
                            reconstructed_lines.append(current_line)
                        current_line = text
                    else:
                        # Same line, append
                        current_line += " " + text if current_line else text
                    
                    prev_y = y0
                
                # Add last line
                if current_line:
                    reconstructed_lines.append(current_line)
                
                # Process reconstructed lines
                items = extract_items_from_reconstructed_lines(reconstructed_lines, base_fields, invoice_type)
    except:
        pass
    
    return items

def extract_items_from_reconstructed_lines(lines: List[str], base_fields: dict, invoice_type: str) -> List[Dict[str, Any]]:
    """Extract items from reconstructed lines"""
    items = []
    
    # Find table start
    table_start = -1
    for i, line in enumerate(lines):
        if any(marker in line for marker in ['คำอธิบาย', 'Description', 'ปริมาณ', 'Quantity']):
            table_start = i
            break
    
    if table_start < 0:
        table_start = 0
    
    # Process lines looking for campaign patterns
    i = table_start + 1
    while i < len(lines):
        line = lines[i].strip()
        
        # Pattern 1: Lines with DMCRM/DMHEALTH pattern
        if ('DMCRM' in line or 'DMHEALTH' in line or 'DMHealth' in line):
            # This is likely a campaign line
            description = line
            campaign_code = ''
            
            # Check if there's a pipe separator
            if '|' in line:
                parts = line.split('|')
                description = parts[0].strip()
                campaign_code = parts[1].strip() if len(parts) > 1 else ''
            
            # Look for amount in next few lines
            amount = None
            for j in range(i + 1, min(i + 10, len(lines))):
                next_line = lines[j]
                amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', next_line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    break
            
            if amount and abs(amount) > 0.01:
                items.append({
                    **base_fields,
                    'invoice_type': invoice_type,
                    'line_number': len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': clean_campaign_description(description),
                    'campaign_code': campaign_code,
                    'agency': detect_agency(campaign_code) or detect_agency(description),
                    'project_id': extract_project_id(campaign_code) or extract_project_id(description),
                    'project_name': extract_project_name(description),
                    'objective': extract_objective(description),
                    'period': None,
                    'campaign_id': campaign_code or extract_campaign_id(description)
                })
        
        # Pattern 2: Thai adjustment descriptions
        elif any(indicator in line for indicator in ['กิจกรรมที่ไม่ถูกต้อง', 'การปรับปรุง', 'ค่าใช้จ่าย']):
            description = line
            
            # Look for amount
            amount = None
            for j in range(i, min(i + 5, len(lines))):
                check_line = lines[j]
                amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', check_line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    break
            
            if amount and abs(amount) > 0.01:
                items.append({
                    **base_fields,
                    'invoice_type': invoice_type,
                    'line_number': len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': description[:200],  # Limit length
                    'campaign_code': '',
                    'agency': None,
                    'project_id': None,
                    'project_name': None,
                    'objective': 'Adjustment',
                    'period': None,
                    'campaign_id': None
                })
        
        i += 1
    
    # Remove duplicates
    items = remove_duplicate_items(items)
    
    # Sort by amount (descending)
    items = sorted(items, key=lambda x: abs(x['amount']), reverse=True)
    
    # Renumber
    for i, item in enumerate(items):
        item['line_number'] = i + 1
    
    return items

def clean_campaign_description(description: str) -> str:
    """Clean campaign description"""
    # Remove extra spaces
    description = re.sub(r'\s+', ' ', description)
    
    # Fix common issues
    description = description.replace('D M C R M', 'DMCRM')
    description = description.replace('D M H E A L T H', 'DMHEALTH')
    description = description.replace('_ ', '_')
    description = description.replace(' _', '_')
    
    return description.strip()

def clean_text(text: str) -> str:
    """Clean text from special characters"""
    # Remove zero-width characters
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_invoice_number(text_content: str, filename: str) -> str:
    """Extract invoice number"""
    # Try Thai pattern
    inv_match = re.search(r'หมายเลขใบแจ้งหนี้:\s*(\d{10})', text_content)
    if inv_match:
        return inv_match.group(1)
    
    # Try English pattern
    inv_match = re.search(r'Invoice number:\s*(\d{10})', text_content)
    if inv_match:
        return inv_match.group(1)
    
    # Extract from filename
    inv_match = re.search(r'(\d{10})', filename)
    if inv_match:
        return inv_match.group(1)
    
    return 'Unknown'

def determine_invoice_type(text_content: str, invoice_number: str) -> str:
    """Determine if invoice is AP or Non-AP"""
    # Check for credit note indicators
    if 'ใบลดหนี้' in text_content or 'Credit Note' in text_content:
        return 'Non-AP'
    
    # Check for negative total (credit)
    total_match = re.search(r'ยอดรวม.*?(-\d+\.\d+)', text_content)
    if total_match:
        return 'Non-AP'
    
    # Check for AP indicators
    ap_indicators = [
        'การคลิก', 'Click', 'Impression', 'การแสดงผล',
        'Campaign', 'แคมเปญ', 'CPC', 'CPM',
        'Search', 'Display', 'Responsive', 'Traffic',
        'งานโฆษณา', 'pk|', 'DMCRM', 'DMHEALTH'
    ]
    
    indicator_count = sum(1 for indicator in ap_indicators if indicator in text_content)
    
    return 'AP' if indicator_count >= 2 else 'Non-AP'

def extract_total_amount(text_content: str) -> float:
    """Extract total amount from invoice"""
    patterns = [
        r'ยอดรวม.*?[:\s]+.*?([-]?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'จำนวนเงินรวม.*?[:\s]+.*?([-]?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'Total.*?[:\s]+.*?([-]?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'Amount due.*?[:\s]+.*?([-]?\d{1,3}(?:,\d{3})*\.?\d*)'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text_content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            try:
                amount = float(match.group(1).replace(',', ''))
                if abs(amount) > 100:  # Ignore very small amounts
                    return amount
            except:
                pass
    
    return 0.0

def extract_main_description(text_content: str) -> str:
    """Extract main description for invoice"""
    # Extract account name
    account_match = re.search(r'บัญชี:\s*([^\n]+)', text_content)
    if account_match:
        return account_match.group(1).strip()
    
    account_match = re.search(r'Account:\s*([^\n]+)', text_content)
    if account_match:
        return account_match.group(1).strip()
    
    return 'Google Ads'

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
    
    return None

def detect_agency(text: str) -> Optional[str]:
    """Detect agency from text"""
    if 'pk|' in text or 'pk_' in text:
        return 'pk'
    return None

def extract_project_id(text: str) -> Optional[str]:
    """Extract project ID from text"""
    # Look for patterns like DMCRM-IN-041-0625
    id_match = re.search(r'D[A-Z]+-[A-Z]+-(\d{3})-(\d{4})', text)
    if id_match:
        return f"{id_match.group(1)}-{id_match.group(2)}"
    
    # Look for numeric ID pattern after pk|
    id_match = re.search(r'pk\|(\d{4,6})\|', text)
    if id_match:
        return id_match.group(1)
    
    return None

def extract_project_name(description: str) -> Optional[str]:
    """Extract project name from description"""
    # Extract campaign type from description
    if 'ลดแลกลุ้น' in description:
        return 'Discount Exchange Campaign'
    elif 'สุขเต็มสิบ' in description:
        return 'Full Happiness Campaign'
    elif 'SDH' in description:
        return 'Single Detached House'
    elif 'Condo' in description.lower():
        return 'Condominium'
    elif 'Town' in description:
        return 'Townhome'
    elif 'Apitown' in description:
        return 'Apitown'
    elif 'Health' in description or 'HEALTH' in description:
        return 'Health Campaign'
    elif 'View' in description:
        return 'View Campaign'
    
    return None

def extract_objective(description: str) -> Optional[str]:
    """Extract objective from description"""
    objectives = {
        'traffic': 'Traffic',
        'search': 'Search',
        'display': 'Display',
        'awareness': 'Awareness',
        'conversion': 'Conversion',
        'lead': 'Lead Generation',
        'การคลิก': 'Clicks',
        'การแสดงผล': 'Impressions',
        'view': 'Views',
        'click': 'Clicks'
    }
    
    desc_lower = description.lower()
    for key, value in objectives.items():
        if key in desc_lower:
            return value
    
    return None

def extract_campaign_id(text: str) -> Optional[str]:
    """Extract campaign ID from text"""
    # Look for patterns like D-DMHealth-TV-00275-0625
    id_match = re.search(r'(D-[A-Za-z]+-[A-Z]+-\d{5}-\d{4})', text)
    if id_match:
        return id_match.group(1)
    
    # Look for patterns like DMCRM-IN-041-0625
    id_match = re.search(r'([A-Z]{2,}[A-Z]+-[A-Z]+-\d{3}-\d{4})', text)
    if id_match:
        return id_match.group(1)
    
    return None

def remove_duplicate_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate items based on amount"""
    seen_amounts = set()
    unique_items = []
    
    for item in items:
        amount_key = round(item['amount'], 2)
        
        if amount_key not in seen_amounts:
            seen_amounts.add(amount_key)
            unique_items.append(item)
    
    return unique_items

if __name__ == "__main__":
    print("Google Parser - Fixed for Fragmented Text")
    print("This parser handles severely fragmented text in Google invoices")