#!/usr/bin/env python3
"""
Facebook parser to achieve 100% accuracy by handling the exact line structure
"""

import re
from typing import Dict, List, Any

def parse_facebook_invoice_100(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Facebook invoice with 100% accuracy"""
    
    # Determine invoice type
    has_st_marker = '[ST]' in text_content
    has_pk_pattern = 'pk|' in text_content
    invoice_type = "AP" if (has_st_marker and has_pk_pattern) else "Non-AP"
    
    # Extract invoice number
    invoice_number = filename.replace('.pdf', '') if filename else 'Unknown'
    invoice_match = re.search(r'Invoice\s+[Nn]umber[\s:]*(\\d{9})', text_content)
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
        items = extract_facebook_ap_100(text_content, base_fields)
    else:
        items = extract_facebook_non_ap_items(text_content, base_fields)
    
    return items

def extract_facebook_ap_100(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Facebook AP items with exact line structure handling"""
    
    items = []
    lines = text_content.split('\n')
    
    # Debug: count line numbers
    line_nums = sum(1 for line in lines if re.match(r'^\d{1,3}$', line.strip()))
    print(f"  Debug: Found {line_nums} potential line numbers")
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this line is just a number (line number)
        if re.match(r'^\\d{1,3}$', line):
            line_num = int(line)
            
            # Look ahead to build the complete item
            j = i + 1
            pk_lines = []
            amount = None
            
            # Collect lines until we find the amount
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Check if this is an amount line (number with decimal, may have spaces)
                amount_match = re.match(r'^([\\d,]+\\.\\d{2})\\s*$', next_line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    break
                
                # Check if we hit next line number
                elif re.match(r'^\\d{1,3}$', next_line) and j > i + 1:
                    break
                
                # Otherwise, it's part of the pk pattern
                elif next_line:
                    pk_lines.append(next_line)
                
                j += 1
            
            # Process if we found both pattern and amount
            if pk_lines and amount is not None and amount > 0:
                # Join the pk lines
                full_pattern = ' '.join(pk_lines)
                
                # Remove platform prefix
                full_pattern = re.sub(r'^(Instagram|Facebook)\\s*-\\s*', '', full_pattern)
                
                # Extract the pk pattern
                pk_match = re.search(r'(pk\\|[^\\[]+\\[ST\\]\\|[A-Z0-9]+)', full_pattern)
                if pk_match:
                    pk_pattern = pk_match.group(1)
                    
                    # Parse AP fields
                    ap_fields = parse_facebook_ap_pattern_100(pk_pattern)
                    
                    item = {
                        **base_fields,
                        'invoice_type': 'AP',
                        'line_number': line_num,
                        'amount': amount,
                        'total': amount,
                        'description': pk_pattern,
                        **ap_fields
                    }
                    items.append(item)
                
                # Move to next item
                i = j
                continue
        
        i += 1
    
    return sorted(items, key=lambda x: x.get('line_number', 999))

def parse_facebook_ap_pattern_100(pattern: str) -> Dict[str, str]:
    """Parse Facebook AP pattern with all variations"""
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown', 
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    # Clean pattern
    pattern = re.sub(r'\\s+', ' ', pattern.replace('\\n', ' ').strip())
    
    # Extract campaign_id (after [ST]|)
    if '[ST]|' in pattern:
        parts = pattern.split('[ST]|')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            # Extract just the campaign ID
            campaign_id_match = re.match(r'^([A-Z0-9]+)', campaign_id)
            if campaign_id_match:
                result['campaign_id'] = campaign_id_match.group(1)
        pattern = parts[0]  # Work with part before [ST]
    
    # Split by pipes
    parts = pattern.split('|')
    
    if len(parts) >= 2:
        # Second part - project ID
        second_part = parts[1] if len(parts) > 1 else ''
        
        # Direct numeric ID
        if re.match(r'^\\d+$', second_part):
            result['project_id'] = second_part
        
        # Extract details from remaining parts
        if len(parts) > 2:
            details = '|'.join(parts[2:])
            
            # Extract project name
            if 'single-detached-house' in details:
                result['project_name'] = 'Single Detached House'
            elif 'townhome' in details.lower():
                result['project_name'] = 'Townhome'
            elif 'condominium' in details:
                result['project_name'] = 'Condominium'
            elif 'Corporate' in details:
                result['project_name'] = 'Corporate'
            elif 'OnlineMKT' in details:
                result['project_name'] = 'Online Marketing'
            
            # Extract specific project names
            if 'centro-' in details:
                result['project_name'] = 'Centro'
            elif 'moden-' in details:
                result['project_name'] = 'Moden'
            elif 'the-palazzo' in details:
                result['project_name'] = 'The Palazzo'
            elif 'pleno' in details.lower():
                result['project_name'] = 'Pleno'
            elif 'town-avenue' in details:
                result['project_name'] = 'Town Avenue'
            elif 'the-city' in details:
                result['project_name'] = 'The City'
            
            # Extract objective
            objectives = ['Awareness', 'Conversion', 'LeadAd', 'Traffic', 'Engagement', 'View', 'VDO']
            for obj in objectives:
                if obj in details:
                    if obj == 'VDO':
                        result['objective'] = 'View'
                    else:
                        result['objective'] = obj
                    break
            
            # Extract period
            period_patterns = [
                (r'(Q[1-4]Y\\d{2})', None),          # Q2Y25
                (r'Y\\d{2}-([A-Z]{3}\\d{2})', 1),    # Y25-JUN25
                (r'([A-Z]{3}\\d{2})', None),         # JUN25
                (r'([A-Z][a-z]{2}\\d{2})', None),    # Jun25
                (r'Y25-([A-Z]{3})', 1),             # Y25-JUN
            ]
            
            for pattern, group in period_patterns:
                period_match = re.search(pattern, details)
                if period_match:
                    if group is not None:
                        result['period'] = period_match.group(group)
                    else:
                        result['period'] = period_match.group(0)
                    break
    
    return result

def extract_facebook_non_ap_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Facebook Non-AP items"""
    
    items = []
    lines = text_content.split('\\n')
    
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
                if re.match(r'^[\\d,]+\\.\\d{2}\\s*$', next_line):
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
    # Test with all 10 invoices
    import fitz
    
    test_files = {
        "246543739.pdf": 1985559.44,
        "246546622.pdf": 973675.24,
        "246578231.pdf": 94498.17,
        "246649305.pdf": 28316.47,
        "246727587.pdf": 1066985.58,
        "246738919.pdf": 788488.72,
        "246774670.pdf": 553692.93,
        "246791975.pdf": 1417663.24,
        "246865374.pdf": 506369.23,
        "246952437.pdf": 163374.47
    }
    
    print("Testing Facebook Parser with 100% Accuracy Goal")
    print("="*60)
    
    total_expected = 0
    total_extracted = 0
    
    for filename, expected_total in test_files.items():
        filepath = f"../Invoice for testing/{filename}"
        try:
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            items = parse_facebook_invoice_100(text, filename)
            total = sum(item['amount'] for item in items)
            accuracy = (total / expected_total * 100) if expected_total > 0 else 0
            
            print(f"\\n{filename}:")
            print(f"  Expected: {expected_total:,.2f}")
            print(f"  Extracted: {total:,.2f}")
            print(f"  Accuracy: {accuracy:.2f}%")
            print(f"  Items: {len(items)}")
            
            total_expected += expected_total
            total_extracted += total
            
            if accuracy < 100:
                diff = expected_total - total
                print(f"  Missing: {diff:,.2f} THB")
                
        except Exception as e:
            print(f"\\n{filename}: ERROR - {str(e)}")
    
    overall_accuracy = (total_extracted / total_expected * 100) if total_expected > 0 else 0
    print(f"\\n{'='*60}")
    print(f"OVERALL RESULTS:")
    print(f"Total Expected: {total_expected:,.2f}")
    print(f"Total Extracted: {total_extracted:,.2f}")
    print(f"Overall Accuracy: {overall_accuracy:.2f}%")