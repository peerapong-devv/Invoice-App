#!/usr/bin/env python3
"""
Final Facebook parser fix to handle all pattern variations
"""

import re
from typing import Dict, List, Any

def parse_facebook_invoice_final(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Facebook invoice with complete pattern handling"""
    
    # Determine invoice type
    has_st_marker = '[ST]' in text_content
    has_pk_pattern = 'pk|' in text_content
    invoice_type = "AP" if (has_st_marker and has_pk_pattern) else "Non-AP"
    
    # Extract invoice number
    invoice_number = filename.replace('.pdf', '') if filename else 'Unknown'
    invoice_match = re.search(r'Invoice\s+[Nn]umber[:\s]*(\d{9})', text_content)
    if invoice_match:
        invoice_number = invoice_match.group(1)
    
    # Base fields
    base_fields = {
        'platform': 'Facebook',
        'filename': filename,
        'invoice_number': invoice_number,
        'invoice_id': invoice_number
    }
    
    if invoice_type == "AP":
        items = extract_facebook_ap_items_final(text_content, base_fields)
    else:
        items = extract_facebook_non_ap_items(text_content, base_fields)
    
    return items

def extract_facebook_ap_items_final(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract all Facebook AP items including edge cases"""
    
    items = []
    lines = text_content.split('\n')
    
    # Method 1: Find pk| patterns with amounts on same line
    # Pattern: amount line_num platform pk|...[ST]|id
    pattern1 = r'([\d,]+\.?\d*)\s+(\d+)\s+(?:Instagram|Facebook)?\s*-?\s*(pk\|[^\[]+\[ST\]\|[A-Z0-9]+)'
    
    for match in re.finditer(pattern1, text_content):
        amount_str = match.group(1)
        line_num = match.group(2)
        pk_pattern = match.group(3)
        
        try:
            amount = float(amount_str.replace(',', ''))
            ap_fields = parse_facebook_ap_pattern_complete(pk_pattern)
            
            item = {
                **base_fields,
                'invoice_type': 'AP',
                'line_number': int(line_num),
                'amount': amount,
                'total': amount,
                'description': pk_pattern,
                **ap_fields
            }
            items.append(item)
        except:
            continue
    
    # Method 2: Find patterns where amount is after [ST]
    # Pattern: pk|...[ST]|id amount
    pattern2 = r'(pk\|[^\[]+\[ST\]\|[A-Z0-9]+)\s+([\d,]+\.?\d*)'
    
    existing_descriptions = {item['description'] for item in items}
    
    for match in re.finditer(pattern2, text_content):
        pk_pattern = match.group(1)
        amount_str = match.group(2)
        
        # Skip if already found
        if pk_pattern in existing_descriptions:
            continue
            
        try:
            amount = float(amount_str.replace(',', ''))
            ap_fields = parse_facebook_ap_pattern_complete(pk_pattern)
            
            item = {
                **base_fields,
                'invoice_type': 'AP',
                'line_number': len(items) + 1,
                'amount': amount,
                'total': amount,
                'description': pk_pattern,
                **ap_fields
            }
            items.append(item)
        except:
            continue
    
    # Method 3: Find amounts that appear after line breaks
    # Look for patterns split across lines
    for i, line in enumerate(lines):
        if 'pk|' in line and '[ST]' in line:
            # Check if this line has amount
            if not re.search(r'[\d,]+\.?\d{2}', line):
                # Look for amount in next few lines
                for j in range(1, 4):  # Check next 3 lines
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        amount_match = re.match(r'^([\d,]+\.?\d{2})$', next_line)
                        if amount_match:
                            # Extract pk pattern from original line
                            pk_match = re.search(r'(pk\|[^\[]+\[ST\]\|[A-Z0-9]+)', line)
                            if pk_match:
                                pk_pattern = pk_match.group(1)
                                if pk_pattern not in existing_descriptions:
                                    try:
                                        amount = float(amount_match.group(1).replace(',', ''))
                                        ap_fields = parse_facebook_ap_pattern_complete(pk_pattern)
                                        
                                        item = {
                                            **base_fields,
                                            'invoice_type': 'AP',
                                            'line_number': len(items) + 1,
                                            'amount': amount,
                                            'total': amount,
                                            'description': pk_pattern,
                                            **ap_fields
                                        }
                                        items.append(item)
                                        existing_descriptions.add(pk_pattern)
                                    except:
                                        pass
                            break
    
    return sorted(items, key=lambda x: x.get('line_number', 0))

def parse_facebook_ap_pattern_complete(pattern: str) -> Dict[str, str]:
    """Parse all variations of Facebook AP patterns"""
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown', 
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    # Clean pattern - remove newlines
    pattern = pattern.replace('\n', '')
    
    # Extract campaign_id (after [ST]|)
    if '[ST]|' in pattern:
        parts = pattern.split('[ST]|')
        if len(parts) > 1:
            result['campaign_id'] = parts[1].strip()
        pattern = parts[0]  # Work with part before [ST]
    
    # Split by first pipe after pk
    if '|' in pattern:
        parts = pattern.split('|', 2)  # Split into max 3 parts
        
        if len(parts) >= 2:
            # Second part analysis
            second_part = parts[1]
            
            # Pattern 1: Direct numeric project ID (e.g., "40093")
            if re.match(r'^\d+$', second_part):
                result['project_id'] = second_part
                # Details in third part
                if len(parts) > 2:
                    parse_details_section(parts[2], result)
            
            # Pattern 2: SDH_pk_40093_... (project ID embedded)
            elif '_pk_' in second_part:
                # Extract project ID after _pk_
                id_match = re.search(r'_pk_(\d+)', second_part)
                if id_match:
                    result['project_id'] = id_match.group(1)
                # Parse remaining details
                parse_details_section(second_part, result)
                if len(parts) > 2:
                    parse_details_section(parts[2], result)
            
            # Pattern 3: TH_pk_40084-BANGYAI-DISTRICT_...
            elif 'TH_pk_' in second_part or 'SDH_pk_' in second_part or 'CD_pk_' in second_part:
                # Extract project ID
                id_match = re.search(r'pk_(\d+)', second_part)
                if id_match:
                    result['project_id'] = id_match.group(1)
                # Parse project name and details
                parse_details_section(second_part, result)
                if len(parts) > 2:
                    parse_details_section(parts[2], result)
            
            # Pattern 4: Corporate_pk_Corporate...
            elif 'Corporate' in second_part:
                result['project_id'] = 'Corporate'
                result['project_name'] = 'Corporate'
                parse_details_section(second_part, result)
            
            # Pattern 5: OnlineMKT
            elif 'OnlineMKT' in second_part:
                result['project_id'] = 'OnlineMKT'
                result['project_name'] = 'Online Marketing'
                parse_details_section(second_part, result)
            
            # Pattern 6: Just project type (SDH, TH, CD)
            elif second_part in ['SDH', 'TH', 'CD']:
                result['project_id'] = second_part
                result['project_name'] = {
                    'SDH': 'Single Detached House',
                    'TH': 'Townhome',
                    'CD': 'Condominium'
                }.get(second_part, second_part)
                if len(parts) > 2:
                    parse_details_section(parts[2], result)
    
    return result

def parse_details_section(details: str, result: dict):
    """Parse the details section for project name, objective, and period"""
    
    # Clean details
    details = details.replace('\n', '')
    
    # Extract project name if not already set
    if result['project_name'] == 'Unknown':
        # Pattern 1: th-single-detached-house-...
        if 'single-detached-house' in details:
            result['project_name'] = 'Single Detached House'
        elif 'townhome' in details.lower() or 'town' in details.lower():
            result['project_name'] = 'Townhome'
        elif 'condominium' in details:
            result['project_name'] = 'Condominium'
        # Pattern 2: BANGYAI-DISTRICT_APTOWNHOME_TH_PlenoTown...
        elif 'APTOWNHOME' in details:
            result['project_name'] = 'AP Townhome'
        elif 'DISTRICT' in details:
            # Extract district name
            district_match = re.search(r'([A-Z\-]+)-DISTRICT', details)
            if district_match:
                result['project_name'] = district_match.group(1) + ' District'
        # Pattern 3: After dash or underscore
        elif '-' in details or '_' in details:
            # Extract potential project name
            parts = details.replace('_', '-').split('-')
            for part in parts:
                if len(part) > 3 and not part.isupper() and not part.isdigit():
                    result['project_name'] = part
                    break
    
    # Extract objective
    objectives = ['Awareness', 'Conversion', 'LeadAd', 'Traffic', 'Engagement', 'View']
    for obj in objectives:
        if obj in details:
            result['objective'] = obj
            break
    
    # Extract period with multiple patterns
    period_patterns = [
        r'(Q[1-4]Y\d{2})',           # Q2Y25
        r'([A-Z]{3}\d{2})',           # JUN25
        r'Y\d{2}-([A-Z]{3}\d{2})',   # Y25-JUN25
        r'([A-Z][a-z]{2}\d{2})',      # Jun25
        r'-([A-Z][a-z]{2})-',         # -Jun-
        r'_([A-Z]{3})_',              # _JUN_
        r'([A-Z]{3})-',               # JUN-
    ]
    
    for pattern in period_patterns:
        period_match = re.search(pattern, details)
        if period_match:
            result['period'] = period_match.group(1)
            break

def extract_facebook_non_ap_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Facebook Non-AP items (keeping existing working logic)"""
    
    items = []
    lines = text_content.split('\n')
    
    # Find ar@meta.com marker
    start_idx = -1
    for i, line in enumerate(lines):
        if 'ar@meta.com' in line:
            start_idx = i
            break
    
    if start_idx == -1:
        return []
    
    # Extract line items after marker
    i = start_idx + 1
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if it's a line number
        if line.isdigit():
            line_num = int(line)
            
            # Collect description (next 1-3 lines)
            description_parts = []
            j = i + 1
            
            while j < len(lines) and j < i + 10:
                next_line = lines[j].strip()
                
                # Stop if we hit amount or next line number
                if re.match(r'^[\d,]+\.\d{2}\s*$', next_line):
                    # Found amount
                    try:
                        amount = float(next_line.replace(',', ''))
                        
                        item = {
                            **base_fields,
                            'invoice_type': 'Non-AP',
                            'line_number': line_num,
                            'description': ' '.join(description_parts),
                            'amount': amount,
                            'total': amount
                        }
                        items.append(item)
                        i = j
                        break
                    except:
                        pass
                elif next_line.isdigit():
                    # Hit next line number
                    i = j - 1
                    break
                elif next_line:
                    # Part of description
                    description_parts.append(next_line)
                
                j += 1
            
            if j >= len(lines) or j >= i + 10:
                i = j
        
        i += 1
    
    return items

if __name__ == "__main__":
    # Test specific invoices
    import fitz
    
    test_files = {
        "246543739.pdf": 1985559.44,
        "246546622.pdf": 973675.24,
        "246578231.pdf": 94498.17,
        "246727587.pdf": 1066985.58,
        "246738919.pdf": 788488.72,
        "246774670.pdf": 553692.93,
        "246791975.pdf": 1417663.24,
        "246865374.pdf": 506369.23
    }
    
    for filename, expected_total in test_files.items():
        filepath = f"../Invoice for testing/{filename}"
        try:
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            items = parse_facebook_invoice_final(text, filename)
            total = sum(item['amount'] for item in items)
            accuracy = (total / expected_total * 100) if expected_total > 0 else 0
            
            print(f"\n{filename}:")
            print(f"  Expected: {expected_total:,.2f}")
            print(f"  Extracted: {total:,.2f}")
            print(f"  Accuracy: {accuracy:.2f}%")
            print(f"  Items: {len(items)}")
            
            if len(items) > 0:
                # Show sample item
                item = items[0]
                print(f"  Sample: {item.get('project_id')} - {item.get('objective')} - {item.get('period')}")
        except Exception as e:
            print(f"\n{filename}: ERROR - {str(e)}")