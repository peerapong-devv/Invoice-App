#!/usr/bin/env python3
"""
Facebook AP parser that learns from TikTok's successful approach
"""

import re
from typing import Dict, List, Any

def parse_facebook_invoice_with_tiktok_approach(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """
    Parse Facebook invoice using TikTok's successful approach
    """
    
    # Determine invoice type
    has_st_marker = '[ST]' in text_content
    has_pk_pattern = 'pk|' in text_content
    invoice_type = "AP" if (has_st_marker and has_pk_pattern) else "Non-AP"
    
    # Extract invoice number
    invoice_number = filename.replace('.pdf', '') if filename else 'Unknown'
    invoice_match = re.search(r'Invoice\s+[Nn]umber[:\s]*(\\d{9})', text_content)
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
        return extract_facebook_ap_items_tiktok_style(text_content, base_fields)
    else:
        # Keep existing Non-AP logic (it works well)
        return extract_facebook_non_ap_items(text_content, base_fields)

def extract_facebook_ap_items_tiktok_style(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """
    Extract Facebook AP items using TikTok's approach
    """
    
    line_items = []
    
    # First, clean up the text to handle line breaks
    # Facebook splits long lines, so we need to reconstruct them
    lines = text_content.split('\\n')
    reconstructed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # If line starts with a number and contains Instagram/Facebook prefix
        if re.match(r'^\\d+\\s+(Instagram|Facebook|pk)', line):
            # This is a potential line item start
            full_line = line
            
            # Check if the pattern continues on next lines
            j = i + 1
            while j < len(lines) and j < i + 5:  # Max 5 lines to prevent runaway
                next_line = lines[j].strip()
                
                # If next line starts with amount or contains [ST], we're done
                if re.match(r'^[\\d,]+\\.\\d{2}', next_line) or '[ST]' in next_line:
                    break
                    
                # Otherwise, it might be continuation
                if next_line and not re.match(r'^\\d+\\s+(Instagram|Facebook)', next_line):
                    full_line += ' ' + next_line
                    j += 1
                else:
                    break
            
            reconstructed_lines.append(full_line)
            i = j
        else:
            reconstructed_lines.append(line)
            i += 1
    
    # Now extract [ST] patterns with amounts
    # Pattern: number + platform + pk|...[ST]|campaign_id + amount
    # Facebook often has amount before the pattern
    pattern = r'([\\d,]+\\.\\d{2})\\s+(\\d+)\\s+(.+?\\[ST\\]\\|[A-Z0-9]+)'
    
    text_reconstructed = '\\n'.join(reconstructed_lines)
    matches = re.findall(pattern, text_reconstructed)
    
    for amount_str, line_num, campaign_str in matches:
        try:
            amount = float(amount_str.replace(',', ''))
        except:
            continue
        
        # Clean the campaign string
        campaign_str = campaign_str.strip()
        
        # Remove platform prefix
        for prefix in ['Instagram - ', 'Facebook - ', 'Instagram-', 'Facebook-']:
            if campaign_str.startswith(prefix):
                campaign_str = campaign_str[len(prefix):].strip()
                break
        
        # Parse using TikTok's approach
        ap_fields = parse_facebook_ap_pattern_tiktok_style(campaign_str)
        
        item = {
            **base_fields,
            'invoice_type': 'AP',
            'line_number': int(line_num),
            'amount': amount,
            'total': amount,
            'description': campaign_str,
            **ap_fields
        }
        
        line_items.append(item)
    
    # If we didn't get enough items, try alternative extraction
    if len(line_items) < 50:  # Facebook AP typically has many items
        # Look for pk| patterns without line numbers
        pk_pattern = r'(pk\\|[^\\[]+\\[ST\\]\\|[A-Z0-9]+)'
        pk_matches = re.findall(pk_pattern, text_reconstructed)
        
        # Match with nearby amounts
        for pk_str in pk_matches:
            # Check if we already have this pattern
            if any(pk_str in item.get('description', '') for item in line_items):
                continue
                
            # Find amount after this pattern
            escaped_pattern = re.escape(pk_str)
            amount_after = re.search(escaped_pattern + r'\\s*([\\d,]+\\.\\d{2})', text_reconstructed)
            
            if amount_after:
                try:
                    amount = float(amount_after.group(1).replace(',', ''))
                    ap_fields = parse_facebook_ap_pattern_tiktok_style(pk_str)
                    
                    item = {
                        **base_fields,
                        'invoice_type': 'AP',
                        'amount': amount,
                        'total': amount,
                        'description': pk_str,
                        **ap_fields
                    }
                    
                    line_items.append(item)
                except:
                    continue
    
    return sorted(line_items, key=lambda x: x.get('line_number', 999))

def parse_facebook_ap_pattern_tiktok_style(pattern: str) -> Dict[str, str]:
    """
    Parse Facebook AP pattern using TikTok's successful approach
    
    Pattern examples:
    pk|40022|SDH_pk_th-single-detached-house-centro-onnut-suvarnabhumi_none_Awareness_VDO_FBAWARENESSQ2Y25_[ST]|2089P22
    pk|OnlineMKT_pk_AP-AWO-Content_none_Engagement_facebook_Boostpost_FB-AWO-NationalDay-Post3-Jun_[ST]|1909A02
    """
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown',
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    if not pattern or not pattern.startswith('pk|'):
        return result
    
    # Extract campaign_id first (after [ST]| marker)
    if '[ST]|' in pattern:
        st_split = pattern.split('[ST]|')
        if len(st_split) > 1:
            campaign_id_part = st_split[1].strip()
            # Extract just the campaign ID
            id_match = re.match(r'([A-Z0-9]+)', campaign_id_part)
            if id_match:
                result['campaign_id'] = id_match.group(1)
        # Work with the part before [ST]
        main_pattern = st_split[0]
    else:
        main_pattern = pattern
    
    # Split by pipes
    parts = main_pattern.split('|')
    
    if len(parts) >= 3:
        # Second part is either project_id or special pattern
        second_part = parts[1]
        
        # Check if it's a numeric project ID
        if re.match(r'^\\d+$', second_part):
            result['project_id'] = second_part
            # Third part contains details
            if len(parts) > 2:
                details = parts[2]
                parse_details(details, result)
        
        # Check if it's OnlineMKT pattern
        elif 'OnlineMKT' in second_part:
            result['project_id'] = 'OnlineMKT'
            result['project_name'] = 'OnlineMKT'
            # Parse remaining details
            if '_pk_' in second_part:
                sub_parts = second_part.split('_pk_')
                if len(sub_parts) > 1:
                    result['project_name'] = sub_parts[1].split('_')[0]
        
        # Other patterns
        else:
            # Could be like TH|TH_pk_...
            result['project_id'] = second_part.split('_')[0] if '_' in second_part else second_part
            if len(parts) > 2:
                parse_details(parts[2], result)
    
    return result

def parse_details(details: str, result: dict):
    """Parse details section for project info and objective"""
    
    # Split by underscores
    detail_parts = details.split('_')
    
    # Look for objectives
    objectives = ['Awareness', 'Conversion', 'LeadAd', 'Traffic', 'Engagement', 'View']
    for part in detail_parts:
        if part in objectives:
            result['objective'] = part
            break
    
    # Look for project type
    if 'SDH' in details:
        result['project_name'] = 'Single Detached House'
    elif 'TH' in details and 'townhome' in details:
        result['project_name'] = 'Townhome'
    elif 'CD' in details and 'condominium' in details:
        result['project_name'] = 'Condominium'
    
    # Look for period (Q2Y25, MAY25, etc.)
    period_match = re.search(r'(Q[1-4]Y\\d{2}|[A-Z]{3}\\d{2}|Y\\d{2})', details)
    if period_match:
        result['period'] = period_match.group(1)

def extract_facebook_non_ap_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Keep existing Non-AP extraction logic"""
    # This would be the same as the working Non-AP extraction
    # from truly_fixed_facebook_parser.py
    return []  # Placeholder

if __name__ == "__main__":
    # Test the parser
    import fitz
    
    filename = "246543739.pdf"
    filepath = f"../Invoice for testing/{filename}"
    
    with fitz.open(filepath) as doc:
        text = ''
        for page in doc:
            text += page.get_text()
    
    items = parse_facebook_invoice_with_tiktok_approach(text, filename)
    
    print(f"Extracted {len(items)} items")
    print(f"Total: {sum(item['amount'] for item in items):,.2f} THB")
    
    # Show first 5 items with AP fields
    print("\\nFirst 5 items with AP fields:")
    for i, item in enumerate(items[:5], 1):
        print(f"\\n{i}. Line {item.get('line_number', '?')}")
        print(f"   Amount: {item['amount']:,.2f}")
        print(f"   Agency: {item.get('agency')}")
        print(f"   Project ID: {item.get('project_id')}")
        print(f"   Campaign ID: {item.get('campaign_id')}")
        print(f"   Objective: {item.get('objective')}")