#!/usr/bin/env python3
"""
Truly fixed Facebook parser that extracts ALL line items correctly
"""

import re
from typing import Dict, List, Any
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def parse_facebook_invoice_truly_fixed(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """
    Parse Facebook invoice with complete line item extraction
    """
    
    # Determine invoice type
    has_st_marker = '[ST]' in text_content
    has_pk_pattern = 'pk|' in text_content
    invoice_type = "AP" if (has_st_marker and has_pk_pattern) else "Non-AP"
    
    logger.debug(f"Facebook {filename}: Type={invoice_type}, has_st={has_st_marker}, has_pk={has_pk_pattern}")
    
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
    
    # Extract line items based on type
    if invoice_type == "AP":
        line_items = extract_facebook_ap_line_items_complete(text_content, base_fields)
    else:
        line_items = extract_facebook_non_ap_line_items_complete(text_content, base_fields)
    
    # Extract invoice total for verification
    total_amount = extract_facebook_total(text_content)
    calculated_total = sum(item.get('amount', 0) for item in line_items)
    
    logger.debug(f"Facebook {filename}: Extracted {len(line_items)} items, total={calculated_total:.2f}, invoice_total={total_amount:.2f}")
    
    # If no line items found or total mismatch, create single record
    if not line_items or abs(calculated_total - total_amount) > 1.0:
        logger.warning(f"Facebook {filename}: Fallback to single total record")
        record = {
            **base_fields,
            'invoice_type': invoice_type,
            'description': f'Facebook {invoice_type} Invoice Total',
            'amount': total_amount,
            'total': total_amount
        }
        if invoice_type == "AP":
            record.update({
                'agency': 'pk',
                'project_id': 'Unknown',
                'project_name': 'Unknown',
                'objective': 'Unknown',
                'period': 'Unknown',
                'campaign_id': 'Unknown'
            })
        line_items = [record]
    
    return line_items

def extract_facebook_ap_line_items_complete(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract ALL AP line items from Facebook invoice using [ST] markers"""
    
    line_items = []
    
    # Method 1: Find all [ST] patterns with amounts
    # Pattern: anything ending with [ST]|campaign_id followed by amount
    st_pattern = r'([^[]+\[ST\]\|[A-Z0-9]+)\s+([0-9,]+\.[0-9]{2})'
    
    matches = re.findall(st_pattern, text_content)
    logger.debug(f"Found {len(matches)} [ST] patterns")
    
    for campaign_str, amount_str in matches:
        try:
            amount = float(amount_str.replace(',', ''))
        except:
            continue
        
        # Extract full pk| pattern
        pk_match = re.search(r'(pk\|[^[]+)', campaign_str)
        if pk_match:
            pk_pattern = pk_match.group(1)
            
            # Parse AP fields
            ap_fields = parse_facebook_ap_pattern_complete(pk_pattern + campaign_str[pk_match.end():])
            
            # Extract campaign ID
            campaign_id_match = re.search(r'\[ST\]\|([A-Z0-9]+)', campaign_str)
            if campaign_id_match:
                ap_fields['campaign_id'] = campaign_id_match.group(1)
            
            item = {
                **base_fields,
                'invoice_type': 'AP',
                'amount': amount,
                'total': amount,
                'description': campaign_str,
                **ap_fields
            }
            
            line_items.append(item)
    
    # Method 2: If method 1 didn't find enough, try line-by-line approach
    if len(line_items) < 50:  # Facebook AP invoices typically have many items
        lines = text_content.split('\n')
        
        for i, line in enumerate(lines):
            if 'pk|' in line and '[ST]' in line:
                # Look for amount on same line or next few lines
                amount = None
                
                # Check same line
                amount_match = re.search(r'([0-9,]+\.[0-9]{2})\s*$', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                else:
                    # Check next 3 lines
                    for j in range(1, 4):
                        if i + j < len(lines):
                            next_line = lines[i + j].strip()
                            if re.match(r'^[0-9,]+\.[0-9]{2}$', next_line):
                                amount = float(next_line.replace(',', ''))
                                break
                
                if amount and amount > 0:
                    # Extract pk pattern
                    pk_match = re.search(r'(pk\|[^[]+\[ST\]\|[A-Z0-9]+)', line)
                    if pk_match:
                        campaign_str = pk_match.group(1)
                        
                        # Check if we already have this amount
                        if not any(item['amount'] == amount for item in line_items):
                            ap_fields = parse_facebook_ap_pattern_complete(campaign_str)
                            
                            item = {
                                **base_fields,
                                'invoice_type': 'AP',
                                'amount': amount,
                                'total': amount,
                                'description': campaign_str,
                                **ap_fields
                            }
                            
                            line_items.append(item)
    
    return sorted(line_items, key=lambda x: x.get('amount', 0), reverse=True)

def extract_facebook_non_ap_line_items_complete(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract ALL Non-AP line items from Facebook invoice"""
    
    line_items = []
    lines = text_content.split('\n')
    
    # Method 1: Look for table structure with Line#, Description, Amount
    # Pattern: number at start, text with |, amount at end
    table_pattern = r'^(\d{1,3})\s+(.+?\|.+?)\s+([0-9,]+\.[0-9]{2})$'
    
    for line in lines:
        match = re.match(table_pattern, line)
        if match:
            try:
                line_num = int(match.group(1))
                description = match.group(2).strip()
                amount = float(match.group(3).replace(',', ''))
                
                if amount > 0:
                    item = {
                        **base_fields,
                        'invoice_type': 'Non-AP',
                        'line_number': line_num,
                        'description': description,
                        'amount': amount,
                        'total': amount
                    }
                    line_items.append(item)
            except:
                continue
    
    # Method 2: Multi-line structure (line number, then description, then amount)
    if len(line_items) < 20:  # Non-AP invoices typically have many items
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if line is just a number (line number)
            if line.isdigit() and 1 <= int(line) <= 999:
                line_num = int(line)
                
                # Look for description and amount in next lines
                description = None
                amount = None
                
                for j in range(1, 10):  # Check next 10 lines
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        
                        # Description contains | and letters
                        if not description and '|' in next_line and any(c.isalpha() for c in next_line):
                            description = next_line
                        
                        # Amount is just numbers with decimal
                        if not amount and re.match(r'^[0-9,]+\.[0-9]{2}$', next_line):
                            try:
                                amount = float(next_line.replace(',', ''))
                            except:
                                pass
                        
                        # If we have both, create item
                        if description and amount:
                            # Check if this combination already exists
                            exists = any(
                                item['line_number'] == line_num and 
                                abs(item['amount'] - amount) < 0.01 
                                for item in line_items
                            )
                            
                            if not exists and amount > 0:
                                item = {
                                    **base_fields,
                                    'invoice_type': 'Non-AP',
                                    'line_number': line_num,
                                    'description': description,
                                    'amount': amount,
                                    'total': amount
                                }
                                line_items.append(item)
                            break
                
                i += j if description and amount else 1
            else:
                i += 1
    
    # Remove duplicates based on line number
    unique_items = {}
    for item in line_items:
        line_num = item.get('line_number', 0)
        if line_num not in unique_items or item['amount'] > unique_items[line_num]['amount']:
            unique_items[line_num] = item
    
    return sorted(unique_items.values(), key=lambda x: x.get('line_number', 0))

def parse_facebook_ap_pattern_complete(pattern: str) -> Dict[str, str]:
    """Parse Facebook AP pattern to extract all fields"""
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown',
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    # Extract campaign ID
    campaign_match = re.search(r'\[ST\]\|([A-Z0-9]+)', pattern)
    if campaign_match:
        result['campaign_id'] = campaign_match.group(1)
    
    # Clean pattern
    clean_pattern = re.sub(r'\[ST\]\|[A-Z0-9]+', '', pattern)
    
    # Split by pipe
    parts = clean_pattern.split('|')
    
    if len(parts) >= 2:
        # Parse based on pattern type
        second_part = parts[1]
        
        # Type 1: Numeric project ID
        if re.match(r'^\d+$', second_part):
            result['project_id'] = second_part
            if len(parts) > 2:
                details = parts[2]
                # Extract project name
                name_match = re.search(r'_pk_([^_]+)', details)
                if name_match:
                    result['project_name'] = name_match.group(1)
                # Extract objective
                for obj in ['Traffic', 'Awareness', 'View', 'Engagement', 'LeadAd', 'Conversion']:
                    if obj in details:
                        result['objective'] = obj
                        break
                # Extract period
                period_match = re.search(r'(Q[1-4]Y\d{2}|Y\d{2}-[A-Z]{3}\d{2}|[A-Z]{3}\d{2})', details)
                if period_match:
                    result['period'] = period_match.group(1)
        
        # Type 2: OnlineMKT pattern
        elif 'OnlineMKT' in second_part:
            result['project_id'] = 'OnlineMKT'
            sub_parts = second_part.split('_')
            if len(sub_parts) > 2:
                result['project_name'] = sub_parts[2]
            # Extract objective and period from remaining parts
            for part in sub_parts:
                if part in ['Engagement', 'View', 'Traffic', 'Awareness']:
                    result['objective'] = part
                elif re.match(r'[A-Z][a-z]{2}\d*', part):
                    result['period'] = part
        
        # Type 3: Corporate pattern
        elif 'Corporate' in second_part:
            result['project_id'] = 'Corporate'
            result['project_name'] = 'Corporate'
            if 'View' in second_part:
                result['objective'] = 'View'
        
        # Type 4: Pattern with _pk_ in second part
        elif '_pk_' in second_part:
            # Extract ID after _pk_
            id_match = re.search(r'_pk_(\d+)', second_part)
            if id_match:
                result['project_id'] = id_match.group(1)
            # Get project type prefix
            prefix_match = re.match(r'^([A-Z]+)_pk_', second_part)
            if prefix_match:
                result['project_name'] = prefix_match.group(1)
    
    return result

def extract_facebook_total(text_content: str) -> float:
    """Extract total amount from Facebook invoice"""
    
    # Try various patterns
    patterns = [
        r'Invoice\s+Total[:\s]*([0-9,]+\.[0-9]{2})',
        r'Subtotal[:\s]*([0-9,]+\.[0-9]{2})',
        r'Total\s+Due[:\s]*([0-9,]+\.[0-9]{2})',
        r'Total\s+Amount\s+Due[:\s]*([0-9,]+\.[0-9]{2})',
        r'รวมจำนวนเงินทั้งสิ้น[:\s]*([0-9,]+\.[0-9]{2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                continue
    
    return 0.0