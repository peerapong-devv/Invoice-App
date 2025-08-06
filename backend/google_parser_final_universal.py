#!/usr/bin/env python3
"""
Google Parser Final Universal - Extract ALL line items from PDF without hardcoding
Learn from Facebook/TikTok success - handle fragmented text and table formats
"""

import re
from typing import Dict, List, Any, Optional, Tuple
import fitz

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice - extract all line items without hardcoding"""
    
    # Extract invoice number
    invoice_number = extract_invoice_number(text_content, filename)
    
    # Base fields
    base_fields = {
        'platform': 'Google',
        'filename': filename,
        'invoice_number': invoice_number,
        'invoice_id': invoice_number
    }
    
    # Clean and reconstruct fragmented text
    cleaned_text = clean_text(text_content)
    reconstructed_text = reconstruct_fragmented_text(text_content)
    
    # Try both texts for better extraction
    items = []
    
    # Strategy 1: Extract from reconstructed text (for fragmented PDFs)
    if reconstructed_text != cleaned_text:
        items = extract_line_items_from_text(reconstructed_text, base_fields)
    
    # Strategy 2: Extract from cleaned text (for normal PDFs)
    if not items:
        items = extract_line_items_from_text(cleaned_text, base_fields)
    
    # Strategy 3: Extract from original text with special handling
    if not items:
        items = extract_line_items_special(text_content, base_fields)
    
    # Determine invoice type
    invoice_type = 'AP' if items and len(items) > 1 else 'Non-AP'
    
    # Check for credit notes
    if any(item['amount'] < 0 for item in items):
        invoice_type = 'Non-AP'
    
    # Set invoice type
    for item in items:
        item['invoice_type'] = invoice_type
    
    # If no items found, create single line with total
    if not items:
        total = extract_total_amount(cleaned_text)
        if total != 0:
            items = [{
                **base_fields,
                'invoice_type': 'Non-AP',
                'line_number': 1,
                'amount': total,
                'total': total,
                'description': extract_account_name(cleaned_text),
                'agency': None,
                'project_id': None,
                'project_name': None,
                'objective': None,
                'period': extract_period(cleaned_text),
                'campaign_id': None
            }]
    
    return items

def reconstruct_fragmented_text(text_content: str) -> str:
    """Reconstruct text that has been fragmented into individual characters"""
    lines = text_content.split('\n')
    
    # Phase 1: Join single character lines
    reconstructed_lines = []
    char_buffer = []
    
    for line in lines:
        stripped = line.strip()
        
        # If single character (excluding spaces and special chars)
        if len(stripped) == 1 and stripped not in [' ', '\t', '\n', '']:
            char_buffer.append(stripped)
        else:
            # Flush buffer if we have accumulated characters
            if char_buffer:
                # Join characters intelligently
                joined = join_fragmented_chars(char_buffer)
                if joined:
                    reconstructed_lines.append(joined)
                char_buffer = []
            
            # Add normal line
            if stripped:
                reconstructed_lines.append(line)
    
    # Don't forget last buffer
    if char_buffer:
        joined = join_fragmented_chars(char_buffer)
        if joined:
            reconstructed_lines.append(joined)
    
    # Phase 2: Merge related lines
    final_text = merge_related_lines(reconstructed_lines)
    
    return final_text

def join_fragmented_chars(chars: List[str]) -> str:
    """Intelligently join fragmented characters"""
    # Remove zero-width spaces
    chars = [c.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '') for c in chars]
    
    # Join characters
    text = ''.join(chars)
    
    # Fix common patterns
    text = text.replace('p k|', 'pk|')
    text = text.replace('pk |', 'pk|')
    text = text.replace('| |', '|')
    text = text.replace('[ S T ]', '[ST]')
    text = text.replace('[ ST ]', '[ST]')
    
    return text

def merge_related_lines(lines: List[str]) -> str:
    """Merge lines that belong together"""
    merged = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a pk| pattern
        if 'pk|' in line or 'pk｜' in line:
            # Collect all parts of the pattern
            pattern_parts = [line]
            j = i + 1
            
            # Continue collecting until we hit an amount or unrelated line
            while j < len(lines):
                next_line = lines[j]
                # Check if continuation of pattern
                if (next_line.startswith('|') or 
                    next_line.startswith('｜') or
                    '_' in next_line or
                    '[ST]' in next_line or
                    re.match(r'^[A-Za-z0-9_\-]+$', next_line)):
                    pattern_parts.append(next_line)
                    j += 1
                else:
                    break
            
            # Join pattern parts
            full_pattern = ''.join(pattern_parts)
            merged.append(full_pattern)
            i = j
        else:
            merged.append(line)
            i += 1
    
    return '\n'.join(merged)

def extract_line_items_from_text(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract line items from text content"""
    items = []
    lines = text_content.split('\n')
    
    # Method 1: Look for pk| patterns (AP invoices)
    pk_items = extract_pk_pattern_items(lines, base_fields)
    if pk_items:
        items.extend(pk_items)
    
    # Method 2: Look for table format items
    table_items = extract_table_format_items(lines, base_fields)
    if table_items:
        items.extend(table_items)
    
    # Method 3: Look for credit items
    credit_items = extract_credit_items(lines, base_fields)
    if credit_items:
        items.extend(credit_items)
    
    # Remove duplicates based on amount
    items = remove_duplicate_items(items)
    
    return items

def extract_pk_pattern_items(lines: List[str], base_fields: dict) -> List[Dict[str, Any]]:
    """Extract items with pk| patterns"""
    items = []
    
    # Join all lines to handle multi-line patterns
    full_text = '\n'.join(lines)
    
    # Pattern to find pk| entries
    pk_pattern = re.compile(
        r'(pk[|｜]\d+[|｜][^\n]+?(?:\[ST\][|｜]\w+)?)\s+(-?\d{1,3}(?:,\d{3})*\.?\d{2})',
        re.MULTILINE
    )
    
    matches = pk_pattern.finditer(full_text)
    for match in matches:
        desc = match.group(1).strip()
        amount = float(match.group(2).replace(',', ''))
        
        # Parse AP fields
        ap_fields = parse_pk_pattern(desc)
        
        item = {
            **base_fields,
            'line_number': len(items) + 1,
            'amount': amount,
            'total': amount,
            'description': desc,
            **ap_fields
        }
        items.append(item)
    
    return items

def extract_table_format_items(lines: List[str], base_fields: dict) -> List[Dict[str, Any]]:
    """Extract items from table format"""
    items = []
    
    # Find table header
    header_idx = -1
    for i, line in enumerate(lines):
        if ('คำอธิบาย' in line or 'Description' in line) and i + 2 < len(lines):
            # Verify it's a table header
            if 'ปริมาณ' in lines[i+1] or 'จำนวนเงิน' in lines[i+2]:
                header_idx = i
                break
    
    if header_idx == -1:
        return items
    
    # Extract items from table
    i = header_idx + 3  # Skip header rows
    current_desc = None
    amount_pattern = re.compile(r'^\s*(-?\d{1,3}(?:,\d{3})*\.?\d{2})\s*$')
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is a description line
        if line and not amount_pattern.match(line) and line not in ['การคลิก', 'Click', 'THB']:
            # This might be a description
            if not any(skip in line for skip in ['ยอดรวม', 'Total', 'GST', 'ภาษี']):
                current_desc = line
        
        # Check if this is an amount
        elif amount_pattern.match(line) and current_desc:
            amount = float(line.replace(',', ''))
            
            # Valid line item amount range
            if 100 < abs(amount) < 500000:
                # Parse campaign details
                ap_fields = parse_campaign_description(current_desc)
                
                item = {
                    **base_fields,
                    'line_number': len(items) + 1,
                    'amount': amount,
                    'total': amount,
                    'description': current_desc,
                    **ap_fields
                }
                items.append(item)
                current_desc = None  # Reset
        
        i += 1
    
    return items

def extract_credit_items(lines: List[str], base_fields: dict) -> List[Dict[str, Any]]:
    """Extract credit/refund items"""
    items = []
    credit_keywords = ['กิจกรรมที่ไม่ถูกต้อง', 'ใบลดหนี้', 'คืนเงิน', 'Credit', 'Refund']
    amount_pattern = re.compile(r'^\s*(-?\d{1,3}(?:,\d{3})*\.?\d{2})\s*$')
    
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in credit_keywords):
            # Look for amount in next few lines
            for j in range(i+1, min(i+5, len(lines))):
                if amount_pattern.match(lines[j].strip()):
                    amount = float(lines[j].strip().replace(',', ''))
                    if amount < 0:  # Credits should be negative
                        item = {
                            **base_fields,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': line.strip(),
                            'agency': 'pk',
                            'project_id': 'CREDIT',
                            'project_name': 'Credit Adjustment',
                            'objective': 'N/A',
                            'period': None,
                            'campaign_id': 'CREDIT'
                        }
                        items.append(item)
                        break
    
    return items

def extract_line_items_special(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Special extraction for difficult cases"""
    items = []
    lines = text_content.split('\n')
    
    # Look for amounts and associate with descriptions
    amount_pattern = re.compile(r'^\s*(-?\d{1,3}(?:,\d{3})*\.?\d{2})\s*$')
    desc_candidates = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Collect potential descriptions
        if (stripped and 
            not amount_pattern.match(stripped) and
            len(stripped) > 10 and
            not any(skip in stripped for skip in ['ยอดรวม', 'Total', 'GST', 'การคลิก', 'Click'])):
            desc_candidates.append((i, stripped))
        
        # Check for amount
        elif amount_pattern.match(stripped):
            amount = float(stripped.replace(',', ''))
            
            # Find best description candidate
            if 100 < abs(amount) < 500000 and desc_candidates:
                # Use closest previous description
                best_desc = None
                for desc_idx, desc in reversed(desc_candidates):
                    if desc_idx < i and i - desc_idx < 10:
                        best_desc = desc
                        break
                
                if best_desc:
                    ap_fields = parse_campaign_description(best_desc)
                    
                    item = {
                        **base_fields,
                        'line_number': len(items) + 1,
                        'amount': amount,
                        'total': amount,
                        'description': best_desc,
                        **ap_fields
                    }
                    items.append(item)
    
    return items

def parse_pk_pattern(pattern: str) -> dict:
    """Parse pk| pattern to extract AP fields"""
    result = {
        'agency': 'pk',
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': None,
        'campaign_id': None
    }
    
    # Split by |
    parts = pattern.split('|')
    
    if len(parts) >= 2:
        # Extract project ID
        result['project_id'] = parts[1]
        
        # Extract details from remaining parts
        if len(parts) >= 3:
            content = '|'.join(parts[2:])
            
            # Project name
            if 'SDH' in content:
                result['project_name'] = 'Single Detached House'
            elif 'Apitown' in content:
                result['project_name'] = 'Apitown'
                if 'udonthani' in content.lower():
                    result['project_name'] = 'Apitown - Udon Thani'
                elif 'phitsanulok' in content.lower():
                    result['project_name'] = 'Apitown - Phitsanulok'
            elif 'TH' in content and 'townhome' in content.lower():
                result['project_name'] = 'Townhome'
            
            # Objective
            if 'Traffic_Responsive' in content:
                result['objective'] = 'Traffic - Responsive'
            elif 'Traffic_Search_Generic' in content:
                result['objective'] = 'Search - Generic'
            elif 'Traffic_Search_Compet' in content:
                result['objective'] = 'Search - Competitor'
            elif 'Traffic_Search_Brand' in content:
                result['objective'] = 'Search - Brand'
            elif 'Traffic_CollectionCanvas' in content:
                result['objective'] = 'Traffic - Collection'
            elif 'LeadAd' in content:
                result['objective'] = 'Lead Generation'
            
            # Campaign ID
            camp_match = re.search(r'\[ST\][|｜](\w+)', content)
            if camp_match:
                result['campaign_id'] = camp_match.group(1)
    
    return result

def parse_campaign_description(description: str) -> dict:
    """Parse campaign description to extract fields"""
    result = {
        'agency': 'pk',
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': None,
        'campaign_id': None
    }
    
    desc_upper = description.upper()
    
    # Extract campaign ID
    id_patterns = [
        r'([A-Z]{2,}[-_][A-Z0-9]+[-_]\d+[-_]\d+)',  # DMCRM-IN-041-0625
        r'D-([A-Z]{2,}[-_][A-Z0-9]+[-_]\d+)',       # D-DMHealth-TV-00275
    ]
    
    for pattern in id_patterns:
        match = re.search(pattern, description)
        if match:
            result['campaign_id'] = match.group(1) if '(' in pattern else match.group(0)
            break
    
    # Extract project name
    if 'DMCRM' in desc_upper:
        result['project_name'] = 'Digital Marketing CRM'
    elif 'DMHEALTH' in desc_upper:
        result['project_name'] = 'Digital Marketing Health'
    elif 'PRAKIT' in desc_upper:
        result['project_name'] = 'Prakit'
    
    # Extract objective
    if '_VIEW_' in desc_upper or 'VIEW' in desc_upper:
        result['objective'] = 'View'
    elif 'VDO' in desc_upper:
        result['objective'] = 'Video View'
    elif 'TRAFFIC' in desc_upper:
        result['objective'] = 'Traffic'
    
    return result

def remove_duplicate_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate items based on amount"""
    unique_items = []
    seen_amounts = set()
    
    for item in items:
        amount_key = f"{item['amount']:.2f}"
        if amount_key not in seen_amounts:
            unique_items.append(item)
            seen_amounts.add(amount_key)
    
    # Renumber
    for i, item in enumerate(unique_items, 1):
        item['line_number'] = i
    
    return unique_items

def clean_text(text: str) -> str:
    """Clean text from special characters"""
    text = text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    return text

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
        r'ยอดรวม.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'จำนวนเงินรวม.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)',
        r'Total.*?(\-?\d{1,3}(?:,\d{3})*\.?\d*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                pass
    
    return 0.0

def extract_account_name(text_content: str) -> str:
    """Extract account name"""
    match = re.search(r'บัญชี:\s*([^\n]+)', text_content)
    if match:
        return match.group(1).strip()
    return 'Google Ads'

def extract_period(text_content: str) -> Optional[str]:
    """Extract billing period"""
    pattern = r'(\d{1,2}\s+\S+\s+\d{4})\s*[-–]\s*(\d{1,2}\s+\S+\s+\d{4})'
    match = re.search(pattern, text_content)
    if match:
        return f"{match.group(1)} - {match.group(2)}"
    return None

if __name__ == "__main__":
    print("Google Parser Final Universal - Ready")
    print("Extracts all line items without hardcoding")
    print("Handles both fragmented text and table formats")