#!/usr/bin/env python3
"""
Google Parser Complete - Fixes all issues:
1. Doesn't include subtotals/totals as line items
2. Extracts AP fields when available
3. Includes fees from last page
4. Handles text fragmentation
"""

import re
from typing import Dict, List, Any, Optional
import fitz
import os

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice with complete accuracy"""
    
    # Extract invoice number
    invoice_number = extract_invoice_number(text_content, filename)
    
    # Base fields
    base_fields = {
        'platform': 'Google',
        'filename': filename if isinstance(filename, str) else 'Unknown',
        'invoice_number': invoice_number,
        'invoice_id': invoice_number
    }
    
    # Try to get items from PDF if possible
    items = []
    if os.path.exists(filename):
        pdf_path = filename
    else:
        # Try to find the file
        possible_paths = [
            filename,
            os.path.join('..', 'Invoice for testing', os.path.basename(filename)),
            os.path.join('Invoice for testing', os.path.basename(filename))
        ]
        pdf_path = None
        for path in possible_paths:
            if os.path.exists(path):
                pdf_path = path
                break
    
    if pdf_path:
        items = extract_from_pdf_complete(pdf_path, base_fields)
    
    # If no PDF or no items found, try text extraction
    if not items:
        items = extract_from_text_content(text_content, base_fields)
    
    # Ensure at least one item
    if not items:
        total = extract_total_amount(text_content)
        if total != 0:
            items = [{
                **base_fields,
                'invoice_type': 'Non-AP' if total < 0 else 'AP',
                'line_number': 1,
                'amount': total,
                'total': total,
                'description': 'Google Ads Services',
                'agency': None,
                'project_id': None,
                'project_name': None,
                'objective': None,
                'period': extract_period(text_content),
                'campaign_id': None
            }]
    
    return items

def extract_from_pdf_complete(pdf_path: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract line items from PDF with all fixes"""
    items = []
    
    try:
        with fitz.open(pdf_path) as doc:
            num_pages = len(doc)
            
            # Extract line items from page 2 (if exists)
            if num_pages >= 2:
                items = extract_page2_items(doc[1], base_fields)
            
            # Extract fees from last page
            if num_pages >= 1:
                fee_items = extract_fees_from_last_page(doc[num_pages - 1], base_fields, len(items))
                items.extend(fee_items)
            
    except Exception as e:
        print(f"Error extracting from PDF: {e}")
    
    # Sort by amount (descending) and renumber
    items = sorted(items, key=lambda x: abs(x['amount']), reverse=True)
    for i, item in enumerate(items):
        item['line_number'] = i + 1
    
    return items

def extract_page2_items(page, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract line items from page 2, avoiding totals/subtotals"""
    items = []
    
    text = page.get_text()
    text = text.replace('\u200b', '')  # Remove zero-width spaces
    lines = text.split('\n')
    
    # Skip header lines (usually first 10-15 lines contain subtotals)
    table_start = find_table_start(lines)
    
    # Track seen amounts to avoid duplicates
    seen_amounts = {}
    
    # Process lines looking for line items
    i = table_start
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this line contains an amount
        amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})', line)
        if amount_match:
            amount = float(amount_match.group(1).replace(',', ''))
            
            # Skip unrealistic amounts or zero
            if abs(amount) < 0.01 or abs(amount) > 10000000:
                i += 1
                continue
            
            # Skip if this is in the header area (likely a subtotal)
            if i < table_start + 5:
                i += 1
                continue
            
            # Skip if this line contains total keywords
            if any(keyword in line.lower() for keyword in ['ยอดรวม', 'total', 'จำนวนเงินรวม', 'subtotal']):
                i += 1
                continue
            
            # Extract line item
            item = extract_line_item_complete(lines, i, amount, base_fields, len(items) + 1)
            if item:
                # Check if this is a duplicate amount at same position
                amount_key = f"{amount:.2f}_{i}"
                if amount_key not in seen_amounts:
                    seen_amounts[amount_key] = True
                    items.append(item)
        
        i += 1
    
    return items

def find_table_start(lines: List[str]) -> int:
    """Find where the actual line items table starts"""
    # Look for table headers
    for i, line in enumerate(lines):
        if any(marker in line for marker in ['คำอธิบาย', 'Description', 'รายละเอียด', 'การคลิก', 'Clicks']):
            return i + 1
    
    # Default: skip first 15 lines (usually contains headers/subtotals)
    return 15

def extract_line_item_complete(lines: List[str], amount_line_idx: int, amount: float, 
                               base_fields: dict, line_number: int) -> Optional[Dict[str, Any]]:
    """Extract a complete line item with all fields"""
    
    # Look for description components before the amount
    description_parts = []
    campaign_info = {}
    has_pk_pattern = False
    
    # Look backwards from amount line
    for j in range(max(0, amount_line_idx - 20), amount_line_idx):
        check_line = lines[j].strip()
        
        if not check_line:
            continue
        
        # Check for pk| pattern (AP invoice)
        if 'pk|' in check_line:
            has_pk_pattern = True
            description_parts.append(check_line)
            # Extract campaign info from pk pattern
            campaign_info = extract_ap_fields(check_line)
        
        # Check for other relevant content
        elif any(pattern in check_line for pattern in ['|', 'การคลิก', 'Clicks', 'Campaign', 'แคมเปญ']):
            description_parts.append(check_line)
    
    # Build description
    if description_parts:
        description = ' '.join(description_parts[-3:])  # Last 3 relevant parts
    else:
        # Default description based on amount
        if amount < 0:
            description = 'Credit Adjustment'
        else:
            description = 'Google Ads Campaign'
    
    # Determine invoice type
    invoice_type = 'AP' if has_pk_pattern else 'Non-AP'
    
    # Create item
    item = {
        **base_fields,
        'invoice_type': invoice_type,
        'line_number': line_number,
        'amount': amount,
        'total': amount,
        'description': description[:200],  # Limit length
        'agency': campaign_info.get('agency'),
        'project_id': campaign_info.get('project_id'),
        'project_name': campaign_info.get('project_name'),
        'objective': campaign_info.get('objective'),
        'period': campaign_info.get('period'),
        'campaign_id': campaign_info.get('campaign_id')
    }
    
    return item

def extract_ap_fields(text: str) -> Dict[str, Any]:
    """Extract AP fields from pk| pattern"""
    result = {
        'agency': None,
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': None,
        'campaign_id': None
    }
    
    # Check for pk| pattern
    if 'pk|' in text:
        result['agency'] = 'pk'
        
        # Extract project ID
        id_match = re.search(r'pk\s*\|\s*(\d{4,6})\s*\|', text)
        if id_match:
            result['project_id'] = id_match.group(1)
        
        # Extract campaign ID patterns
        campaign_patterns = [
            r'\b(\d{4}[A-Z]\d{2})\b',  # 2089P12
            r'(D-[A-Za-z]+-[A-Z]+-\d{5}-\d{4})',  # D-DMHealth-TV-00275-0625
            r'([A-Z]{2,}-[A-Z]{2}-\d{3}-\d{4})'  # DMCRM-IN-041-0625
        ]
        
        for pattern in campaign_patterns:
            match = re.search(pattern, text)
            if match:
                result['campaign_id'] = match.group(1)
                break
        
        # Extract project name
        if 'SDH' in text:
            result['project_name'] = 'Single Detached House'
        elif 'Apitown' in text:
            result['project_name'] = 'Apitown'
        elif 'DMHEALTH' in text:
            result['project_name'] = 'Health Campaign'
        elif 'DMCRM' in text:
            result['project_name'] = 'CRM Campaign'
        
        # Extract objective
        objectives = {
            'traffic': 'Traffic',
            'search': 'Search',
            'awareness': 'Awareness',
            'การคลิก': 'Clicks',
            'responsive': 'Responsive'
        }
        
        text_lower = text.lower()
        for key, value in objectives.items():
            if key in text_lower:
                result['objective'] = value
                break
    
    return result

def extract_fees_from_last_page(page, base_fields: dict, start_line_num: int) -> List[Dict[str, Any]]:
    """Extract fee items from the last page"""
    items = []
    
    text = page.get_text()
    lines = text.split('\n')
    
    # Look for fee section
    fee_start = -1
    for i, line in enumerate(lines):
        if 'ค่าธรรมเนียม' in line:
            fee_start = i
            break
    
    if fee_start >= 0:
        # Extract fees after the header
        for i in range(fee_start + 1, len(lines)):
            line = lines[i].strip()
            
            # Look for fee amounts
            amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})', line)
            if amount_match:
                amount = float(amount_match.group(1).replace(',', ''))
                
                # Skip if too small
                if abs(amount) < 0.01:
                    continue
                
                # Get description from previous line
                description = 'Fee'
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if prev_line and not prev_line.isdigit():
                        description = prev_line
                
                item = {
                    **base_fields,
                    'invoice_type': 'Non-AP',
                    'line_number': start_line_num + len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': f"Fee - {description}"[:200],
                    'agency': None,
                    'project_id': None,
                    'project_name': None,
                    'objective': None,
                    'period': None,
                    'campaign_id': None
                }
                items.append(item)
    
    return items

def extract_from_text_content(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Fallback extraction from text content"""
    items = []
    
    # Clean text
    text_content = text_content.replace('\u200b', '')
    lines = text_content.split('\n')
    
    # Similar logic as PDF extraction but from text
    table_start = find_table_start(lines)
    
    for i in range(table_start, len(lines)):
        line = lines[i].strip()
        
        amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})', line)
        if amount_match:
            amount = float(amount_match.group(1).replace(',', ''))
            
            # Skip unrealistic amounts
            if abs(amount) < 0.01 or abs(amount) > 10000000:
                continue
            
            # Skip totals
            if any(skip in line.lower() for skip in ['ยอดรวม', 'total', 'จำนวนเงินรวม']):
                continue
            
            # Create item
            item = extract_line_item_complete(lines, i, amount, base_fields, len(items) + 1)
            if item:
                items.append(item)
    
    return items

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
    if isinstance(filename, str):
        inv_match = re.search(r'(\d{10})', filename)
        if inv_match:
            return inv_match.group(1)
    
    return 'Unknown'

def extract_total_amount(text_content: str) -> float:
    """Extract total amount"""
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
                if abs(amount) > 100:
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
    
    return None

if __name__ == "__main__":
    print("Google Parser Complete - Handles all issues")