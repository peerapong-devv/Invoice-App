#!/usr/bin/env python3
"""
Facebook parser to achieve 100% accuracy by handling all edge cases
"""

import re
from typing import Dict, List, Any

def parse_facebook_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
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
        items = extract_facebook_ap(text_content, base_fields)
    else:
        items = extract_facebook_non_ap(text_content, base_fields)
    
    return items

def extract_facebook_ap(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Facebook AP items handling all variations"""
    
    items = []
    lines = text_content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is a line number
        if line.isdigit() and 1 <= int(line) <= 999:
            line_num = int(line)
            
            # Build complete item
            j = i + 1
            pk_lines = []
            amount = None
            
            # Collect lines until amount
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Check for amount (positive or negative)
                amount_match = re.match(r'^(-?[\d,]+\.\d{2})\s*$', next_line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    break
                
                # Check if next line number
                elif next_line.isdigit() and 1 <= int(next_line) <= 999 and j > i + 1:
                    break
                
                # Skip empty lines
                elif not next_line:
                    j += 1
                    continue
                
                # Check for annotations to skip
                elif '- Coupons:' in next_line or 'goodwill/bugs' in next_line:
                    # Skip annotation line
                    j += 1
                    continue
                
                # Otherwise collect as part of pattern
                else:
                    pk_lines.append(next_line)
                
                j += 1
            
            # Process if we have pattern and amount
            if pk_lines and amount is not None:
                # Join pattern lines
                full_pattern = ' '.join(pk_lines)
                
                # Remove platform prefix
                full_pattern = re.sub(r'^(Instagram|Facebook)\s*-\s*', '', full_pattern)
                
                # Handle split campaign IDs (lines starting with |)
                full_pattern = re.sub(r'\s+\|', '|', full_pattern)
                
                # Extract pk pattern
                pk_match = re.search(r'(pk\|[^\[]+\[ST\]\|[A-Z0-9]+)', full_pattern)
                if pk_match:
                    pk_pattern = pk_match.group(1)
                    
                    # Parse AP fields
                    ap_fields = parse_ap_fields(pk_pattern)
                    
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

def parse_ap_fields(pattern: str) -> Dict[str, str]:
    """Parse AP fields from pattern"""
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown', 
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    # Clean pattern
    pattern = re.sub(r'\s+', ' ', pattern.replace('\n', ' ').strip())
    
    # Extract campaign_id (after [ST]|)
    if '[ST]|' in pattern:
        parts = pattern.split('[ST]|')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            # Extract just the ID
            campaign_id_match = re.match(r'^([A-Z0-9]+)', campaign_id)
            if campaign_id_match:
                result['campaign_id'] = campaign_id_match.group(1)
        pattern = parts[0]  # Work with part before [ST]
    
    # Split by pipes
    parts = pattern.split('|')
    
    if len(parts) >= 2:
        # Project ID is second part
        project_id = parts[1]
        
        # Direct numeric ID
        if re.match(r'^\d+$', project_id):
            result['project_id'] = project_id
        # Corporate
        elif project_id == 'Corporate':
            result['project_id'] = 'Corporate'
            result['project_name'] = 'Corporate'
        # OnlineMKT
        elif project_id == 'OnlineMKT':
            result['project_id'] = 'OnlineMKT'
            result['project_name'] = 'Online Marketing'
        
        # Join remaining parts for details
        if len(parts) > 2:
            details = '|'.join(parts[2:])
            
            # Extract project type/name
            if 'SDH' in details or 'single-detached-house' in details:
                result['project_name'] = 'Single Detached House'
            elif 'TH' in details or 'townhome' in details.lower():
                result['project_name'] = 'Townhome'
            elif 'CD' in details or 'condominium' in details:
                result['project_name'] = 'Condominium'
            
            # Extract specific project names
            project_names = {
                'centro-': 'Centro',
                'moden-': 'Moden',
                'the-palazzo': 'The Palazzo',
                'pleno': 'Pleno',
                'town-avenue': 'Town Avenue',
                'the-city': 'The City',
                'life-': 'Life',
                'apitown': 'Apitown'
            }
            
            for key, name in project_names.items():
                if key in details.lower():
                    result['project_name'] = name
                    break
            
            # Extract objective
            objectives = ['Awareness', 'Conversion', 'LeadAd', 'Traffic', 'Engagement', 'View', 'VDO']
            for obj in objectives:
                if obj in details:
                    result['objective'] = 'View' if obj == 'VDO' else obj
                    break
            
            # Extract period
            period_patterns = [
                r'(Q[1-4]Y\d{2})',          # Q2Y25
                r'Y\d{2}-([A-Z]{3}\d{2})',  # Y25-JUN25
                r'([A-Z]{3}\d{2})',          # JUN25
                r'Y25-([A-Z]{3})',           # Y25-JUN
            ]
            
            for pattern_re in period_patterns:
                period_match = re.search(pattern_re, details)
                if period_match:
                    # Get the last group if there are multiple
                    result['period'] = period_match.group(period_match.lastindex or 0)
                    break
    
    return result

def extract_facebook_non_ap(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Facebook Non-AP items"""
    
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
        
        # Check if it's a line number (single digit or up to 3 digits)
        if line.isdigit() and 1 <= int(line) <= 999:
            line_num = int(line)
            
            # Collect description
            description_parts = []
            j = i + 1
            
            while j < len(lines) and j <= i + 10:
                next_line = lines[j].strip()
                
                # Check for amount (with or without spaces)
                amount_match = re.match(r'^([\d,]+\.\d{2})\s*$', next_line)
                if amount_match:
                    # Found amount
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                        
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
                elif next_line.isdigit() and 1 <= int(next_line) <= 999:
                    # Hit next line number
                    i = j - 1
                    break
                elif next_line:
                    # Part of description
                    description_parts.append(next_line)
                
                j += 1
            
            if j > i + 10:
                # Didn't find amount in reasonable range
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
        "246649305.pdf": 20198.70,  # Verified from invoice total
        "246727587.pdf": 1066985.58,
        "246738919.pdf": 788488.72,
        "246774670.pdf": 553692.93,
        "246791975.pdf": 1417663.24,
        "246865374.pdf": 506369.23,
        "246952437.pdf": 163374.47
    }
    
    print("Facebook Parser - 100% Accuracy Goal")
    print("="*60)
    
    total_expected = 0
    total_extracted = 0
    perfect_count = 0
    
    for filename, expected_total in test_files.items():
        filepath = f"../Invoice for testing/{filename}"
        try:
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            items = parse_facebook_invoice(text, filename)
            total = sum(item['amount'] for item in items)
            accuracy = (total / expected_total * 100) if expected_total > 0 else 0
            
            print(f"\n{filename}:")
            print(f"  Expected: {expected_total:,.2f}")
            print(f"  Extracted: {total:,.2f}")
            print(f"  Accuracy: {accuracy:.2f}%")
            print(f"  Items: {len(items)}")
            
            total_expected += expected_total
            total_extracted += total
            
            if accuracy >= 99.99:
                perfect_count += 1
                print(f"  PERFECT!")
            else:
                diff = expected_total - total
                print(f"  Missing: {diff:,.2f} THB")
                
        except Exception as e:
            print(f"\n{filename}: ERROR - {str(e)}")
    
    overall_accuracy = (total_extracted / total_expected * 100) if total_expected > 0 else 0
    print(f"\n{'='*60}")
    print(f"OVERALL RESULTS:")
    print(f"Total Expected: {total_expected:,.2f}")
    print(f"Total Extracted: {total_extracted:,.2f}")
    print(f"Overall Accuracy: {overall_accuracy:.2f}%")
    print(f"Perfect Files: {perfect_count}/10")