#!/usr/bin/env python3
"""
Google Parser using pdfplumber - Better handling of fragmented text
"""

import re
import pdfplumber
from typing import Dict, List, Any, Optional
import sys

sys.stdout.reconfigure(encoding='utf-8')

def parse_google_invoice(pdf_path: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice using pdfplumber for better fragmented text handling"""
    
    # Extract invoice number from filename
    invoice_number = extract_invoice_number(filename)
    
    # Base fields
    base_fields = {
        'platform': 'Google',
        'filename': filename,
        'invoice_number': invoice_number,
        'invoice_id': invoice_number
    }
    
    items = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Process all pages
            for page_num, page in enumerate(pdf.pages):
                # Method 1: Extract text with better handling
                text = page.extract_text()
                if text:
                    # Clean zero-width spaces
                    text = clean_fragmented_text(text)
                    
                    # Try table extraction first
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            table_items = extract_items_from_table(table, base_fields)
                            if table_items:
                                items.extend(table_items)
                    
                    # If no table items, try text-based extraction
                    if not items:
                        text_items = extract_items_from_text(text, base_fields)
                        if text_items:
                            items.extend(text_items)
                
                # Method 2: Character-level reconstruction for fragmented text
                if not items and page.chars:
                    reconstructed_items = reconstruct_from_chars(page.chars, base_fields)
                    if reconstructed_items:
                        items.extend(reconstructed_items)
    
    except Exception as e:
        print(f"Error processing with pdfplumber: {e}")
        # Fallback to basic extraction
        items = [create_fallback_item(base_fields)]
    
    # Determine invoice type
    invoice_type = 'AP' if items and len(items) > 1 else 'Non-AP'
    
    # Set invoice type and calculate total
    total = sum(item['amount'] for item in items)
    for item in items:
        item['invoice_type'] = invoice_type
        item['total'] = total
    
    # Renumber items
    for i, item in enumerate(items, 1):
        item['line_number'] = i
    
    return items

def clean_fragmented_text(text: str) -> str:
    """Clean text from zero-width spaces and other invisible characters"""
    # Remove various zero-width and invisible characters
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f\ufeff]', '', text)
    
    # Fix common fragmentation patterns
    text = re.sub(r'p\s*k\s*\|', 'pk|', text)
    text = re.sub(r'\[\s*S\s*T\s*\]', '[ST]', text)
    
    return text

def reconstruct_from_chars(chars: List[Dict], base_fields: dict) -> List[Dict[str, Any]]:
    """Reconstruct text from individual characters for extremely fragmented PDFs"""
    items = []
    
    # Sort characters by position (top to bottom, left to right)
    sorted_chars = sorted(chars, key=lambda x: (round(x['top']), x['x0']))
    
    # Group characters into lines based on y-position
    lines = []
    current_line = []
    current_y = None
    y_tolerance = 3  # Tolerance for same line
    
    for char in sorted_chars:
        if current_y is None or abs(char['top'] - current_y) <= y_tolerance:
            current_line.append(char)
            current_y = char['top']
        else:
            if current_line:
                # Sort characters in line by x position
                current_line.sort(key=lambda x: x['x0'])
                line_text = ''.join([c['text'] for c in current_line])
                lines.append(line_text)
            current_line = [char]
            current_y = char['top']
    
    # Don't forget last line
    if current_line:
        current_line.sort(key=lambda x: x['x0'])
        line_text = ''.join([c['text'] for c in current_line])
        lines.append(line_text)
    
    # Clean and process reconstructed lines
    full_text = '\n'.join(lines)
    full_text = clean_fragmented_text(full_text)
    
    # Extract items from reconstructed text
    return extract_items_from_text(full_text, base_fields)

def extract_items_from_table(table: List[List], base_fields: dict) -> List[Dict[str, Any]]:
    """Extract items from table data"""
    items = []
    
    if not table or len(table) < 2:
        return items
    
    # Find header row
    header_idx = -1
    for i, row in enumerate(table):
        if row and any(cell and 'คำอธิบาย' in str(cell) for cell in row):
            header_idx = i
            break
    
    if header_idx == -1:
        return items
    
    # Process data rows
    for i in range(header_idx + 1, len(table)):
        row = table[i]
        if not row:
            continue
        
        # Extract description and amount
        description = None
        amount = None
        
        for cell in row:
            if cell:
                cell_str = str(cell).strip()
                # Check for amount
                if re.match(r'^-?\d{1,3}(?:,\d{3})*\.?\d{2}$', cell_str):
                    try:
                        amount = float(cell_str.replace(',', ''))
                    except:
                        pass
                # Check for description patterns
                elif any(pattern in cell_str for pattern in ['DMCRM', 'DMHEALTH', 'pk|', 'D-']):
                    description = clean_fragmented_text(cell_str)
        
        # Create item if we have both description and amount
        if description and amount and 100 < abs(amount) < 500000:
            ap_fields = parse_campaign_description(description)
            
            item = {
                **base_fields,
                'line_number': len(items) + 1,
                'amount': amount,
                'description': description,
                **ap_fields
            }
            items.append(item)
    
    return items

def extract_items_from_text(text: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract items from text content"""
    items = []
    lines = text.split('\n')
    
    # Method 1: Look for pk| patterns
    pk_pattern = re.compile(
        r'(pk[|｜]\d+[|｜][^\n]+?(?:\[ST\][|｜]\w+)?)\s*[\d,]+\s+\w+\s+(-?\d{1,3}(?:,\d{3})*\.?\d{2})',
        re.MULTILINE
    )
    
    for match in pk_pattern.finditer(text):
        desc = match.group(1).strip()
        amount = float(match.group(2).replace(',', ''))
        
        if 100 < abs(amount) < 500000:
            ap_fields = parse_pk_pattern(desc)
            
            item = {
                **base_fields,
                'line_number': len(items) + 1,
                'amount': amount,
                'description': desc,
                **ap_fields
            }
            items.append(item)
    
    # Method 2: Look for campaign patterns (DMCRM, DMHEALTH, etc.)
    for i, line in enumerate(lines):
        if any(pattern in line for pattern in ['DMCRM', 'DMHEALTH', 'PRAKIT']):
            description = clean_fragmented_text(line)
            
            # Look for amount in next few lines
            for j in range(i + 1, min(i + 5, len(lines))):
                amount_match = re.match(r'^(-?\d{1,3}(?:,\d{3})*\.?\d{2})$', lines[j].strip())
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    if 100 < abs(amount) < 500000:
                        ap_fields = parse_campaign_description(description)
                        
                        item = {
                            **base_fields,
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'description': description,
                            **ap_fields
                        }
                        items.append(item)
                        break
    
    # Remove duplicates based on amount
    seen_amounts = set()
    unique_items = []
    for item in items:
        amount_key = f"{item['amount']:.2f}"
        if amount_key not in seen_amounts:
            unique_items.append(item)
            seen_amounts.add(amount_key)
    
    return unique_items

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
    
    # Clean pattern
    pattern = clean_fragmented_text(pattern)
    
    # Extract parts
    parts = pattern.split('|')
    
    if len(parts) >= 2:
        # Project ID is usually the second part
        if parts[1].isdigit():
            result['project_id'] = parts[1]
        
        # Join remaining parts
        if len(parts) > 2:
            content = '|'.join(parts[2:])
            
            # Extract project name
            if 'SDH' in content:
                result['project_name'] = 'Single Detached House'
            elif 'Apitown' in content:
                result['project_name'] = 'Apitown'
            elif 'TH' in content and 'townhome' in content.lower():
                result['project_name'] = 'Townhome'
            elif 'CD' in content and 'condominium' in content.lower():
                result['project_name'] = 'Condominium'
            
            # Extract objective
            objectives = {
                'Traffic_Responsive': 'Traffic - Responsive',
                'Traffic_Search_Generic': 'Search - Generic',
                'Traffic_Search_Compet': 'Search - Competitor',
                'Traffic_Search_Brand': 'Search - Brand',
                'LeadAd': 'Lead Generation',
                'Traffic': 'Traffic',
                'View': 'View'
            }
            
            for key, value in objectives.items():
                if key in content:
                    result['objective'] = value
                    break
            
            # Extract campaign ID (after [ST]|)
            st_match = re.search(r'\[ST\][|｜](\w+)', content)
            if st_match:
                result['campaign_id'] = st_match.group(1)
    
    return result

def parse_campaign_description(description: str) -> dict:
    """Parse campaign description for Non-AP invoices"""
    result = {
        'agency': 'pk',
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': None,
        'campaign_id': None
    }
    
    # Extract campaign ID patterns
    id_match = re.search(r'([A-Z]{2,}[-_][A-Z0-9]+[-_]\d+[-_]\d+)', description)
    if id_match:
        result['campaign_id'] = id_match.group(1)
    
    # Extract project name
    if 'DMCRM' in description:
        result['project_name'] = 'Digital Marketing CRM'
        result['project_id'] = 'DMCRM'
    elif 'DMHEALTH' in description or 'DMHealth' in description:
        result['project_name'] = 'Digital Marketing Health'
        result['project_id'] = 'DMHEALTH'
    elif 'PRAKIT' in description:
        result['project_name'] = 'Prakit'
        result['project_id'] = 'PRAKIT'
    
    # Extract objective
    if '_View_' in description or 'View' in description:
        result['objective'] = 'View'
    elif 'VDO' in description:
        result['objective'] = 'Video View'
    elif 'Traffic' in description:
        result['objective'] = 'Traffic'
    
    return result

def extract_invoice_number(filename: str) -> str:
    """Extract invoice number from filename"""
    inv_match = re.search(r'(\d{10})', filename)
    if inv_match:
        return inv_match.group(1)
    return 'Unknown'

def create_fallback_item(base_fields: dict) -> Dict[str, Any]:
    """Create a fallback item when extraction fails"""
    return {
        **base_fields,
        'line_number': 1,
        'amount': 0.0,
        'description': 'Failed to extract items',
        'agency': None,
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': None,
        'campaign_id': None
    }

if __name__ == "__main__":
    print("Google Parser using pdfplumber - Ready")
    print("Better handling of fragmented text and character reconstruction")