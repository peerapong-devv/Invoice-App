#!/usr/bin/env python3
"""
Google Parser - Complete Line Items Extraction
Fixes issue #8 by extracting ALL line items from every Google invoice
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
    
    # Extract line items
    items = extract_line_items(text_content, base_fields, invoice_type)
    
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
                'agency': 'pk' if invoice_type == 'AP' else None,
                'project_id': None,
                'project_name': None,
                'objective': None,
                'period': extract_period(text_content),
                'campaign_id': None
            }]
    
    return items

def extract_line_items(text_content: str, base_fields: dict, invoice_type: str) -> List[Dict[str, Any]]:
    """Extract all line items from the invoice"""
    items = []
    lines = text_content.split('\n')
    
    # Strategy 1: Find the table section (usually on page 2)
    # Look for table headers
    table_start = -1
    for i, line in enumerate(lines):
        if any(marker in line for marker in [
            'คำอธิบาย', 'Description', 'ปริมาณ', 'Quantity',
            'หน่วย', 'Unit', 'จำนวนเงิน', 'Amount'
        ]):
            table_start = i
            break
    
    if table_start > 0:
        # Extract items from table section
        items = extract_items_from_table(lines[table_start:], base_fields, invoice_type)
    
    # Strategy 2: Find lines with pipe separator and amounts
    if len(items) < 3:  # If we found very few items, try pipe pattern
        for i, line in enumerate(lines):
            # Look for lines with pipe separator
            if '|' in line and i < len(lines) - 1:
                # Check if there's an amount in this line or next few lines
                amount = None
                amount_line_offset = 0
                
                # Check current line first
                amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                else:
                    # Check next few lines
                    for j in range(1, min(5, len(lines) - i)):
                        next_line = lines[i + j]
                        amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', next_line)
                        if amount_match:
                            amount = float(amount_match.group(1).replace(',', ''))
                            amount_line_offset = j
                            break
                
                if amount and abs(amount) > 0.01:
                    # Extract description from pipe pattern
                    parts = line.split('|')
                    if len(parts) >= 2:
                        description = parts[0].strip()
                        campaign_code = parts[1].strip()
                        
                        # Remove amount from campaign code if it's in the same line
                        if amount_match and amount_line_offset == 0:
                            campaign_code = re.sub(r'\s*[-]?\d{1,3}(?:,\d{3})*\.\d{2}.*$', '', campaign_code).strip()
                        
                        # Skip if already captured
                        if any(abs(item['amount'] - amount) < 0.01 for item in items):
                            continue
                        
                        items.append({
                            **base_fields,
                            'invoice_type': invoice_type,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': description,
                            'campaign_code': campaign_code,
                            'agency': detect_agency(campaign_code) or detect_agency(description),
                            'project_id': extract_project_id(campaign_code) or extract_project_id(description),
                            'project_name': extract_project_name(description),
                            'objective': extract_objective(description),
                            'period': None,
                            'campaign_id': campaign_code
                        })
    
    # Strategy 3: Find all lines with amounts as fallback
    if len(items) < 3:
        all_amounts = find_all_amounts(lines)
        
        for line_no, amount, context in all_amounts:
            # Skip if already captured
            if any(abs(item['amount'] - amount) < 0.01 for item in items):
                continue
            
            # Create item from amount and context
            description = extract_description_for_amount(lines, line_no, amount)
            
            if description and abs(amount) > 0.01:
                items.append({
                    **base_fields,
                    'invoice_type': invoice_type,
                    'line_number': len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': description,
                    'agency': detect_agency(description),
                    'project_id': extract_project_id(description),
                    'project_name': extract_project_name(description),
                    'objective': extract_objective(description),
                    'period': None,
                    'campaign_id': extract_campaign_id(description)
                })
    
    # Remove duplicates and sort by amount (descending)
    items = remove_duplicate_items(items)
    items = sorted(items, key=lambda x: abs(x['amount']), reverse=True)
    
    # Renumber items
    for i, item in enumerate(items):
        item['line_number'] = i + 1
    
    return items

def extract_items_from_table(lines: List[str], base_fields: dict, invoice_type: str) -> List[Dict[str, Any]]:
    """Extract items from a table section of lines"""
    items = []
    
    i = 1  # Start after headers
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Look for lines with pipe separator (main pattern)
        if '|' in line:
            # Extract complete item with pipe pattern
            item_data = extract_item_with_pipe(lines, i)
            
            if item_data:
                description_parts = item_data['description'].split('|')
                description = description_parts[0].strip() if description_parts else item_data['description']
                campaign_code = description_parts[1].strip() if len(description_parts) > 1 else ''
                
                items.append({
                    **base_fields,
                    'invoice_type': invoice_type,
                    'line_number': len(items) + 1,
                    'amount': item_data['amount'],
                    'total': item_data['amount'],
                    'description': description,
                    'campaign_code': campaign_code,
                    'agency': detect_agency(campaign_code) or detect_agency(description),
                    'project_id': extract_project_id(campaign_code) or extract_project_id(description),
                    'project_name': extract_project_name(description),
                    'objective': extract_objective(description),
                    'period': None,
                    'campaign_id': campaign_code
                })
                
                i = item_data.get('next_line', i + 1)
                continue
        
        # Look for Thai adjustment descriptions
        elif any(indicator in line for indicator in ['กิจกรรมที่ไม่ถูกต้อง', 'การปรับปรุง', 'ค่าใช้จ่าย']):
            # Extract adjustment item
            item_data = extract_adjustment_item(lines, i)
            
            if item_data:
                items.append({
                    **base_fields,
                    'invoice_type': invoice_type,
                    'line_number': len(items) + 1,
                    'amount': item_data['amount'],
                    'total': item_data['amount'],
                    'description': item_data['description'],
                    'campaign_code': '',
                    'agency': None,
                    'project_id': None,
                    'project_name': None,
                    'objective': 'Adjustment',
                    'period': None,
                    'campaign_id': None
                })
                
                i = item_data.get('next_line', i + 1)
                continue
        
        i += 1
    
    return items

def extract_item_with_pipe(lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
    """Extract an item that contains pipe separator"""
    line = lines[start_idx].strip()
    
    # Check if line contains pipe
    if '|' not in line:
        return None
    
    # Look for amount in the same line
    amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
    if amount_match:
        amount = float(amount_match.group(1).replace(',', ''))
        # Remove amount and everything after it from description
        description = line[:amount_match.start()].strip()
        return {
            'description': description,
            'amount': amount,
            'next_line': start_idx + 1
        }
    
    # If no amount in same line, collect description and look ahead
    description = line
    for i in range(start_idx + 1, min(start_idx + 5, len(lines))):
        next_line = lines[i].strip()
        
        # Check for amount
        amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', next_line)
        if amount_match:
            amount = float(amount_match.group(1).replace(',', ''))
            return {
                'description': description,
                'amount': amount,
                'next_line': i + 1
            }
        
        # Stop if we hit another pipe line
        if '|' in next_line:
            break
    
    return None

def extract_adjustment_item(lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
    """Extract an adjustment item (negative amounts with Thai descriptions)"""
    description_parts = []
    amount = None
    next_idx = start_idx
    
    # Collect description starting from current line
    description_parts.append(lines[start_idx].strip())
    
    # Look for amount in next few lines
    for i in range(start_idx + 1, min(start_idx + 10, len(lines))):
        line = lines[i].strip()
        
        # Check for amount (usually negative)
        amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
        if amount_match:
            amount = float(amount_match.group(1).replace(',', ''))
            next_idx = i + 1
            break
        
        # Stop if we hit a pipe line (new item)
        elif '|' in line:
            break
        
        # Otherwise, it might be part of the description
        elif line and not re.match(r'^[\d,.-]+$', line):
            description_parts.append(line)
    
    if amount is not None:
        return {
            'description': ' '.join(description_parts),
            'amount': amount,
            'next_line': next_idx
        }
    
    return None

def find_all_amounts(lines: List[str]) -> List[tuple]:
    """Find all amounts in the text with their context"""
    amounts = []
    
    for i, line in enumerate(lines):
        # Find amounts in the line
        amount_matches = re.finditer(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)', line)
        
        for match in amount_matches:
            try:
                amount = float(match.group(1).replace(',', ''))
                
                # Skip very small amounts or unrealistic amounts
                if abs(amount) < 0.01 or abs(amount) > 100000000:
                    continue
                
                # Get context (previous non-empty lines)
                context = []
                for j in range(max(0, i - 5), i):
                    if lines[j].strip():
                        context.append(lines[j].strip())
                
                amounts.append((i, amount, context))
            except:
                pass
    
    return amounts

def extract_description_for_amount(lines: List[str], line_no: int, amount: float) -> str:
    """Extract description for a given amount"""
    # Check if description is in the same line
    line = lines[line_no]
    amount_str = f"{amount:,.2f}".replace(',', '')
    
    # Remove amount from line
    desc = line.replace(amount_str, '').strip()
    
    # If not enough description, look at previous lines
    if len(desc) < 10:
        prev_lines = []
        for i in range(max(0, line_no - 5), line_no):
            prev_line = lines[i].strip()
            if prev_line and not re.match(r'^[\d,.-]+$', prev_line):
                prev_lines.append(prev_line)
        
        if prev_lines:
            desc = ' '.join(prev_lines[-2:]) + ' ' + desc
    
    return desc.strip()

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
        'งานโฆษณา', 'pk|'
    ]
    
    indicator_count = sum(1 for indicator in ap_indicators if indicator in text_content)
    
    # Check for multiple amounts (line items)
    amount_pattern = re.compile(r'^\s*\d{1,3}(?:,\d{3})*\.?\d{2}\s*$', re.MULTILINE)
    amounts = amount_pattern.findall(text_content)
    
    return 'AP' if indicator_count >= 2 or len(amounts) > 5 else 'Non-AP'

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

def detect_agency(description: str) -> Optional[str]:
    """Detect agency from description"""
    if 'pk|' in description or 'pk_' in description:
        return 'pk'
    return None

def extract_project_id(description: str) -> Optional[str]:
    """Extract project ID from description"""
    # Look for numeric ID pattern after pk|
    id_match = re.search(r'pk\|(\d{4,6})\|', description)
    if id_match:
        return id_match.group(1)
    
    # Look for standalone numeric ID
    id_match = re.search(r'\b(\d{4,6})\b', description)
    if id_match:
        return id_match.group(1)
    
    return None

def extract_project_name(description: str) -> Optional[str]:
    """Extract project name from description"""
    # Common patterns in descriptions
    if 'SDH' in description:
        return 'Single Detached House'
    elif 'Condo' in description.lower():
        return 'Condominium'
    elif 'Town' in description:
        return 'Townhome'
    elif 'Apitown' in description:
        return 'Apitown'
    
    # Try to extract from pk pattern
    pk_match = re.search(r'pk\|[^|]+\|([^|_]+)', description)
    if pk_match:
        name = pk_match.group(1)
        # Clean up
        name = name.replace('_', ' ').replace('-', ' ')
        return name.title()
    
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
        'การแสดงผล': 'Impressions'
    }
    
    desc_lower = description.lower()
    for key, value in objectives.items():
        if key in desc_lower:
            return value
    
    return None

def extract_campaign_id(description: str) -> Optional[str]:
    """Extract campaign ID from description"""
    # Look for campaign ID patterns
    id_patterns = [
        r'\|([A-Z0-9]{6,})\b',  # After pipe
        r'\b([A-Z0-9]{6,})\b',   # Standalone alphanumeric
        r'Campaign[:\s]+([A-Z0-9]+)',  # After "Campaign"
    ]
    
    for pattern in id_patterns:
        match = re.search(pattern, description)
        if match:
            return match.group(1)
    
    return None

def remove_duplicate_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate items based on description and amount"""
    seen = set()
    unique_items = []
    
    for item in items:
        # Create a key from description (first 50 chars) and amount
        key = (item['description'][:50], round(item['amount'], 2))
        
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    
    return unique_items

if __name__ == "__main__":
    print("Google Parser - Complete Line Items Extraction")
    print("This parser extracts ALL line items from Google invoices")