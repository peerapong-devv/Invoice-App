#!/usr/bin/env python3
"""
Google parser that extracts actual data from invoices instead of using lookup tables
"""

import re
from typing import Dict, List, Any

def parse_google_invoice(text_content: str, filename: str) -> List[Dict[str, Any]]:
    """Parse Google invoice with actual data extraction"""
    
    # Get document number
    document_number = filename.replace('.pdf', '')
    
    # Extract invoice number from text
    invoice_match = re.search(r'หมายเลขใบแจ้งหนี้:\s*(\d+)', text_content)
    if not invoice_match:
        invoice_match = re.search(r'Invoice number:\s*(\d+)', text_content)
    
    invoice_number = invoice_match.group(1) if invoice_match else document_number
    
    # Check if AP or Non-AP
    has_pk = 'pk|' in text_content or 'pk |' in text_content
    invoice_type = "AP" if has_pk else "Non-AP"
    
    # Base fields
    base_fields = {
        'platform': 'Google',
        'filename': filename,
        'invoice_id': invoice_number,
        'invoice_number': invoice_number
    }
    
    if invoice_type == "AP":
        items = extract_google_ap_items(text_content, base_fields)
    else:
        items = extract_google_non_ap_items(text_content, base_fields)
    
    return items

def extract_google_ap_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Google AP items with actual amounts"""
    
    items = []
    lines = text_content.split('\n')
    
    # Look for pk| patterns with amounts
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if line contains pk| pattern
        if 'pk|' in line or 'pk |' in line:
            # Extract the pk pattern
            pk_match = re.search(r'(pk\|[^\s]+)', line)
            if pk_match:
                pk_pattern = pk_match.group(1)
                
                # Look for amount on same line or next lines
                amount = None
                
                # Check same line for amount at end
                amount_match = re.search(r'([\d,]+\.?\d*)\s*$', line)
                if amount_match and ',' in amount_match.group(1):
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                    except:
                        pass
                
                # If no amount on same line, check next few lines
                if amount is None:
                    for j in range(i+1, min(i+5, len(lines))):
                        next_line = lines[j].strip()
                        # Look for standalone amount
                        if re.match(r'^[\d,]+\.?\d*$', next_line) and ',' in next_line:
                            try:
                                amount = float(next_line.replace(',', ''))
                                break
                            except:
                                pass
                
                # If we found an amount, create item
                if amount is not None and amount != 0:
                    ap_fields = parse_google_ap_fields(pk_pattern)
                    
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
        
        i += 1
    
    # Also look for credit/adjustment lines with negative amounts
    for i, line in enumerate(lines):
        if 'กิจกรรมที่ไม่ถูกต้อง' in line or 'Invalid activity' in line:
            # Look for negative amount in next few lines
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                neg_match = re.match(r'^-?([\d,]+\.?\d*)$', next_line)
                if neg_match:
                    try:
                        amount = -abs(float(neg_match.group(1).replace(',', '')))
                        
                        # Extract campaign info from the line
                        campaign_match = re.search(r'pk\|[^\s]+', line)
                        if campaign_match:
                            pk_pattern = campaign_match.group(0)
                            ap_fields = parse_google_ap_fields(pk_pattern)
                        else:
                            ap_fields = {
                                'agency': 'pk',
                                'project_id': 'Adjustment',
                                'project_name': 'Credit/Adjustment',
                                'objective': 'N/A',
                                'period': 'N/A',
                                'campaign_id': 'N/A'
                            }
                        
                        item = {
                            **base_fields,
                            'invoice_type': 'AP',
                            'line_number': len(items) + 1,
                            'amount': amount,
                            'total': amount,
                            'description': f'Credit adjustment: {line[:100]}',
                            **ap_fields
                        }
                        items.append(item)
                        break
                    except:
                        pass
    
    return items

def extract_google_non_ap_items(text_content: str, base_fields: dict) -> List[Dict[str, Any]]:
    """Extract Google Non-AP items with actual total"""
    
    # Look for total amount in various formats
    total_amount = 0.0
    
    # Pattern 1: จำนวนเงินรวมที่ต้องชำระในสกุลเงิน THB (may have negative)
    total_match = re.search(r'จำนวนเงินรวมที่ต้องชำระในสกุลเงิน\s+THB\s*(-?฿?[\d,]+\.?\d*)', text_content)
    if not total_match:
        # Pattern 2: ยอดรวมในสกุลเงิน THB  
        total_match = re.search(r'ยอดรวมในสกุลเงิน\s+THB\s*(-?฿?[\d,]+\.?\d*)', text_content)
    if not total_match:
        # Pattern 3: Total amount in THB
        total_match = re.search(r'Total amount.*THB.*?([\d,]+\.?\d*)', text_content, re.IGNORECASE)
    if not total_match:
        # Pattern 4: Just look for large amounts with THB or ฿
        amounts = re.findall(r'[฿$]?\s*([\d,]+\.?\d*)\s*(?:THB)?', text_content)
        if amounts:
            # Take the largest amount as total
            for amt_str in amounts:
                try:
                    amt = float(amt_str.replace(',', ''))
                    if amt > total_amount:
                        total_amount = amt
                except:
                    pass
    else:
        try:
            amount_str = total_match.group(1)
            # Handle negative sign
            if amount_str.startswith('-'):
                total_amount = -float(amount_str[1:].replace('฿', '').replace(',', ''))
            else:
                total_amount = float(amount_str.replace('฿', '').replace(',', ''))
        except:
            pass
    
    # Create single item with total
    item = {
        **base_fields,
        'invoice_type': 'Non-AP',
        'line_number': 1,
        'description': 'Google Ads Non-AP Invoice',
        'amount': total_amount,
        'total': total_amount,
        'agency': None,
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': None,
        'campaign_id': None
    }
    
    return [item]

def parse_google_ap_fields(pattern: str) -> Dict[str, str]:
    """Parse Google AP fields from pk| pattern"""
    
    result = {
        'agency': 'pk',
        'project_id': 'Unknown',
        'project_name': 'Unknown',
        'objective': 'Unknown',
        'period': 'Unknown',
        'campaign_id': 'Unknown'
    }
    
    # Clean pattern
    pattern = pattern.replace('\n', ' ').strip()
    
    # Extract campaign ID if pattern has [ST]
    if '[ST]|' in pattern:
        parts = pattern.split('[ST]|')
        if len(parts) > 1:
            campaign_id = parts[1].strip()
            # Extract just ID part
            id_match = re.match(r'^([A-Z0-9]+)', campaign_id)
            if id_match:
                result['campaign_id'] = id_match.group(1)
        pattern = parts[0]
    
    # Split by pipes
    parts = pattern.split('|')
    
    if len(parts) >= 2:
        # Part 2: Project ID
        project_part = parts[1]
        
        # Numeric project ID
        if project_part.isdigit():
            result['project_id'] = project_part
        
        # Part 3+: Details
        if len(parts) > 2:
            details = '|'.join(parts[2:])
            
            # Extract project type/name
            if 'SDH' in details or 'single-detached-house' in details:
                result['project_name'] = 'Single Detached House'
            elif 'TH' in details or 'townhome' in details:
                result['project_name'] = 'Townhome'
            elif 'CD' in details or 'condominium' in details:
                result['project_name'] = 'Condominium'
            elif 'Apitown' in details:
                result['project_name'] = 'Apitown'
            elif 'OnlineMKT' in details:
                result['project_id'] = 'OnlineMKT'
                result['project_name'] = 'Online Marketing'
            
            # Extract specific location names
            location_patterns = {
                'centro': 'Centro',
                'ratchapruek': 'Ratchapruek',
                'rama': 'Rama',
                'bangna': 'Bangna',
                'rangsit': 'Rangsit'
            }
            
            for key, name in location_patterns.items():
                if key in details.lower():
                    if result['project_name'] != 'Unknown':
                        result['project_name'] += f' - {name}'
                    break
            
            # Extract objective
            objectives = ['Traffic', 'Awareness', 'Conversion', 'LeadAd', 'Engagement', 'View', 'Responsive']
            for obj in objectives:
                if obj in details:
                    result['objective'] = obj
                    break
            
            # Extract period
            period_patterns = [
                r'(Q[1-4]Y\d{2})',          # Q2Y25
                r'(Y\d{2})',                # Y25
                r'([A-Z]{3}\d{2})',         # JUN25
                r'(GDN[A-Z]*Q[1-4]Y\d{2})' # GDNQ2Y25
            ]
            
            for pattern_re in period_patterns:
                period_match = re.search(pattern_re, details)
                if period_match:
                    result['period'] = period_match.group(1)
                    break
    
    return result

if __name__ == "__main__":
    # Test with sample Google invoices
    import fitz
    import os
    
    print("Testing Google Parser with Data Extraction")
    print("="*60)
    
    # Get some Google invoice files
    invoice_dir = "../Invoice for testing"
    google_files = [f for f in os.listdir(invoice_dir) if f.startswith('5') and f.endswith('.pdf')]
    google_files.sort()
    
    # Test first 5 files
    for filename in google_files[:5]:
        filepath = os.path.join(invoice_dir, filename)
        try:
            with fitz.open(filepath) as doc:
                text = ''
                for page in doc:
                    text += page.get_text()
            
            items = parse_google_invoice(text, filename)
            total = sum(item['amount'] for item in items)
            
            print(f"\n{filename}:")
            print(f"  Invoice type: {items[0]['invoice_type'] if items else 'Unknown'}")
            print(f"  Items: {len(items)}")
            print(f"  Total: {total:,.2f} THB")
            
            # Show first item details
            if items:
                item = items[0]
                if item['invoice_type'] == 'AP':
                    print(f"  First item:")
                    print(f"    Project: {item.get('project_id')} - {item.get('project_name')}")
                    print(f"    Objective: {item.get('objective')}")
                    print(f"    Amount: {item['amount']:,.2f}")
                
        except Exception as e:
            print(f"\n{filename}: ERROR - {str(e)}")