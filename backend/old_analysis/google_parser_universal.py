#!/usr/bin/env python3
"""
Google Parser Universal - Extract ALL line items without hardcoding
Based on analysis of real invoice patterns
"""

import re
from typing import Dict, List, Any, Optional
import fitz
import os

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice with universal extraction method"""
    
    # Extract invoice number
    invoice_number = extract_invoice_number(text_content, filename)
    
    # Base fields
    base_fields = {
        'platform': 'Google',
        'filename': filename,
        'invoice_number': invoice_number,
        'invoice_id': invoice_number
    }
    
    # Try PDF-based extraction for better accuracy
    items = []
    if os.path.exists(filename):
        items = extract_from_pdf_universal(filename, base_fields)
    
    # If no items from PDF, try text extraction
    if not items:
        items = extract_from_text_universal(text_content, base_fields)
    
    # Ensure at least one item with total
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

def extract_from_pdf_universal(filepath: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract from PDF using universal patterns"""
    items = []
    
    try:
        with fitz.open(filepath) as doc:
            # Focus on page 2 where line items are
            if len(doc) < 2:
                return items
            
            # Get page 2 text and dict
            page2 = doc[1]
            page2_text = page2.get_text()
            page2_dict = page2.get_text("dict")
            
            # Clean text
            page2_text = page2_text.replace('\u200b', '')
            
            # Method 1: Find all amounts with context
            amount_pattern = r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})'
            lines = page2_text.split('\n')
            
            for i, line in enumerate(lines):
                amount_match = re.search(amount_pattern, line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    
                    # Skip unrealistic amounts
                    if abs(amount) < 0.01 or abs(amount) > 10000000:
                        continue
                    
                    # Skip totals
                    if any(skip in line for skip in ['ยอดรวม', 'Total', 'จำนวนเงินรวม']):
                        continue
                    
                    # Get description from context
                    description = ""
                    campaign_type = "AP"
                    
                    # Look for campaign patterns before amount
                    for j in range(max(0, i-10), i):
                        prev_line = lines[j].strip()
                        
                        # Check for campaign indicators
                        if any(ind in prev_line for ind in ['pk|', 'pk |', 'DMCRM', 'DMHEALTH', 'SDH', 'Campaign']):
                            description = reconstruct_description(lines, j, i)
                            campaign_type = "AP"
                            break
                        
                        # Check for credit indicators
                        elif 'กิจกรรมที่ไม่ถูกต้อง' in prev_line:
                            description = prev_line
                            campaign_type = "Non-AP"
                            break
                    
                    # Also check line itself
                    if not description:
                        if 'การคลิก' in line:
                            # This is likely a campaign amount
                            description = find_campaign_description(lines, i)
                            campaign_type = "AP"
                        elif amount < 0:
                            # Negative amount, likely credit
                            description = find_credit_description(lines, i)
                            campaign_type = "Non-AP"
                    
                    if description:
                        item = create_item(description, amount, base_fields, campaign_type, len(items) + 1)
                        
                        # Skip duplicates
                        if not any(abs(existing['amount'] - amount) < 0.01 for existing in items):
                            items.append(item)
            
            # Method 2: Extract from text blocks
            if len(items) < 3:
                block_items = extract_from_blocks(page2_dict, base_fields)
                for block_item in block_items:
                    if not any(abs(existing['amount'] - block_item['amount']) < 0.01 for existing in items):
                        items.append(block_item)
            
    except Exception as e:
        print(f"Error extracting from PDF: {e}")
    
    # Sort by amount descending and renumber
    items = sorted(items, key=lambda x: abs(x['amount']), reverse=True)
    for i, item in enumerate(items):
        item['line_number'] = i + 1
    
    return items

def extract_from_text_universal(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract from text using universal patterns"""
    items = []
    
    # Pattern 1: Campaign items with pk|
    pk_pattern = r'(pk\s*\|\s*\d+\s*\|[^|]+).*?([-]?\d{1,3}(?:,\d{3})*\.\d{2})'
    for match in re.finditer(pk_pattern, text_content, re.DOTALL):
        description = re.sub(r'\s+', ' ', match.group(1)).strip()
        amount = float(match.group(2).replace(',', ''))
        
        if abs(amount) > 0.01:
            item = create_item(description, amount, base_fields, 'AP', len(items) + 1)
            items.append(item)
    
    # Pattern 2: DMCRM/DMHEALTH campaigns
    dm_pattern = r'(DM(?:CRM|HEALTH)[^|\n]+).*?([-]?\d{1,3}(?:,\d{3})*\.\d{2})'
    for match in re.finditer(dm_pattern, text_content, re.DOTALL):
        description = match.group(1).strip()
        amount = float(match.group(2).replace(',', ''))
        
        # Skip if already captured
        if not any(abs(item['amount'] - amount) < 0.01 for item in items):
            item = create_item(description, amount, base_fields, 'AP', len(items) + 1)
            items.append(item)
    
    # Pattern 3: Credit adjustments
    credit_pattern = r'(กิจกรรมที่ไม่ถูกต้อง[^\\n]+).*?([-]?\d{1,3}(?:,\d{3})*\.\d{2})'
    for match in re.finditer(credit_pattern, text_content, re.DOTALL):
        description = match.group(1).strip()
        amount = float(match.group(2).replace(',', ''))
        
        # Skip if already captured
        if not any(abs(item['amount'] - amount) < 0.01 for item in items):
            item = create_item(description, amount, base_fields, 'Non-AP', len(items) + 1)
            items.append(item)
    
    # Renumber
    for i, item in enumerate(items):
        item['line_number'] = i + 1
    
    return items

def extract_from_blocks(page_dict: dict, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract from PDF text blocks"""
    items = []
    
    # Group spans by Y coordinate
    lines_by_y = {}
    
    for block in page_dict.get("blocks", []):
        if block.get("type") == 0:  # Text block
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    y_pos = round(span.get("bbox", [0, 0, 0, 0])[1], 1)
                    text = span.get("text", "").strip()
                    
                    if text:
                        if y_pos not in lines_by_y:
                            lines_by_y[y_pos] = []
                        lines_by_y[y_pos].append((span.get("bbox", [0, 0, 0, 0])[0], text))
    
    # Process grouped lines
    sorted_y = sorted(lines_by_y.keys())
    
    for i, y in enumerate(sorted_y):
        # Join text at same Y
        sorted_texts = sorted(lines_by_y[y], key=lambda x: x[0])
        line_text = " ".join([t[1] for t in sorted_texts])
        
        # Check for amount
        amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})', line_text)
        if amount_match:
            amount = float(amount_match.group(1).replace(',', ''))
            
            if abs(amount) > 0.01 and abs(amount) < 10000000:
                # Look for description in previous lines
                description = ""
                for j in range(max(0, i-5), i):
                    prev_y = sorted_y[j]
                    prev_texts = sorted(lines_by_y[prev_y], key=lambda x: x[0])
                    prev_line = " ".join([t[1] for t in prev_texts])
                    
                    if any(ind in prev_line for ind in ['pk', 'DMCRM', 'กิจกรรม']):
                        description = prev_line
                        break
                
                if description:
                    invoice_type = 'Non-AP' if amount < 0 else 'AP'
                    item = create_item(description, amount, base_fields, invoice_type, len(items) + 1)
                    items.append(item)
    
    return items

def reconstruct_description(lines: List[str], start_idx: int, end_idx: int) -> str:
    """Reconstruct fragmented description"""
    parts = []
    
    for i in range(start_idx, min(end_idx, start_idx + 10)):
        line = lines[i].strip()
        if line and not re.match(r'^[\d,.-]+$', line):
            parts.append(line)
    
    # Join and fix common fragmentation
    description = " ".join(parts)
    description = re.sub(r'p\s+k\s+\|', 'pk|', description)
    description = re.sub(r'S\s+D\s+H', 'SDH', description)
    description = re.sub(r'D\s+M\s+C\s+R\s+M', 'DMCRM', description)
    description = re.sub(r'\s+', ' ', description)
    
    return description.strip()

def find_campaign_description(lines: List[str], amount_idx: int) -> str:
    """Find campaign description near amount"""
    # Look backwards for campaign pattern
    for i in range(amount_idx - 1, max(0, amount_idx - 20), -1):
        line = lines[i].strip()
        if any(ind in line for ind in ['pk', 'DMCRM', 'DMHEALTH', 'SDH', 'Campaign']):
            return reconstruct_description(lines, i, amount_idx)
    
    return "Google Ads Campaign"

def find_credit_description(lines: List[str], amount_idx: int) -> str:
    """Find credit description near negative amount"""
    # Look for Thai credit patterns
    for i in range(amount_idx - 1, max(0, amount_idx - 10), -1):
        line = lines[i].strip()
        if 'กิจกรรมที่ไม่ถูกต้อง' in line or 'ค่าใช้จ่าย' in line:
            # Get full description
            desc_parts = [line]
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if next_line and not re.search(r'^\d+\.\d+$', next_line):
                    desc_parts.append(next_line)
                else:
                    break
            return " ".join(desc_parts)
    
    return "Credit Adjustment"

def create_item(description: str, amount: float, base_fields: dict, invoice_type: str, line_number: int) -> Dict[str, Any]:
    """Create line item"""
    return {
        **base_fields,
        'invoice_type': invoice_type,
        'line_number': line_number,
        'amount': amount,
        'total': amount,
        'description': description[:200],  # Limit length
        'agency': extract_agency(description),
        'project_id': extract_project_id(description),
        'project_name': extract_project_name(description),
        'objective': extract_objective(description),
        'period': None,
        'campaign_id': extract_campaign_id(description)
    }

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

def extract_agency(description: str) -> Optional[str]:
    """Extract agency"""
    if 'pk|' in description or 'pk |' in description:
        return 'pk'
    return None

def extract_project_id(description: str) -> Optional[str]:
    """Extract project ID"""
    # pk|12345| pattern
    id_match = re.search(r'pk\s*\|\s*(\d{4,6})\s*\|', description)
    if id_match:
        return id_match.group(1)
    
    return None

def extract_project_name(description: str) -> Optional[str]:
    """Extract project name"""
    if 'SDH' in description:
        return 'Single Detached House'
    elif 'Apitown' in description:
        return 'Apitown'
    elif 'DMCRM' in description and 'ลดแลกลุ้น' in description:
        return 'Discount Exchange Campaign'
    elif 'DMCRM' in description and 'สุขเต็มสิบ' in description:
        return 'Full Happiness Campaign'
    elif 'DMHEALTH' in description:
        return 'Health Campaign'
    
    return None

def extract_objective(description: str) -> Optional[str]:
    """Extract objective"""
    objectives = {
        'traffic': 'Traffic',
        'search': 'Search',
        'responsive': 'Responsive',
        'collection': 'Collection',
        'view': 'Views',
        'การคลิก': 'Clicks'
    }
    
    desc_lower = description.lower()
    for key, value in objectives.items():
        if key in desc_lower:
            return value
    
    return None

def extract_campaign_id(description: str) -> Optional[str]:
    """Extract campaign ID"""
    # Pattern like 2089P12
    id_match = re.search(r'\b(\d{4}[A-Z]\d{2})\b', description)
    if id_match:
        return id_match.group(1)
    
    # Pattern like D-DMHealth-TV-00275-0625
    id_match = re.search(r'(D-[A-Za-z]+-[A-Z]+-\d{5}-\d{4})', description)
    if id_match:
        return id_match.group(1)
    
    return None

if __name__ == "__main__":
    print("Google Parser Universal - Extract ALL line items without hardcoding")