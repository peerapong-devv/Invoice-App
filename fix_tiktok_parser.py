#!/usr/bin/env python3

import re
import os
import sys
from PyPDF2 import PdfReader

def parse_tiktok_invoice_fixed(text_content: str, filename: str):
    """
    Fixed TikTok invoice parser that handles concatenated text
    """
    
    # Clean up text
    text_content = text_content.replace('\u200b', '')
    
    # Extract base fields
    base_fields = {}
    invoice_match = re.search(r"Invoice No\.\s*([\w-]+)", text_content, re.IGNORECASE)
    if invoice_match:
        base_fields["invoice_id"] = invoice_match.group(1).strip()
    
    records = []
    
    # Check if this is an AP invoice
    has_st_pattern = bool(re.search(r'ST\d{10,}', text_content))
    has_pk_pattern = bool(re.search(r'pk\|', text_content))
    is_ap = has_st_pattern and has_pk_pattern
    
    if is_ap:
        records = parse_tiktok_ap_fixed(text_content, filename, base_fields)
    else:
        records = parse_tiktok_non_ap_fixed(text_content, filename, base_fields)
    
    return records

def parse_tiktok_ap_fixed(text_content: str, filename: str, base_fields: dict) -> list:
    """Parse TikTok AP invoice"""
    records = []
    
    # Find consumption details section
    consumption_start = text_content.find('Consumption Details:')
    if consumption_start == -1:
        return records
    
    consumption_text = text_content[consumption_start:]
    
    # Use regex to find all ST patterns with their associated data
    # Pattern: ST followed by 10+ digits
    st_pattern = re.compile(r'(ST\d{10,})')
    
    # Find all ST occurrences
    st_matches = list(st_pattern.finditer(consumption_text))
    
    for i, match in enumerate(st_matches):
        st_id = match.group(1)
        start_pos = match.end()
        
        # Find the end position (next ST or end of text)
        if i + 1 < len(st_matches):
            end_pos = st_matches[i + 1].start()
        else:
            end_pos = len(consumption_text)
        
        # Extract the section for this ST
        section = consumption_text[start_pos:end_pos]
        
        # Look for pk| pattern in this section
        if 'pk|' in section:
            # Extract the campaign description (everything after pk| until amounts)
            pk_start = section.find('pk|')
            campaign_section = section[pk_start:]
            
            # Find amounts in the section (last occurrence of amount pattern)
            amount_matches = re.findall(r'([\d,]+\.\d{2})', campaign_section)
            if amount_matches:
                # The last amount is typically the cash consumption
                amount = float(amount_matches[-1].replace(',', ''))
                
                # Extract campaign description
                # Remove amounts and dates from the end
                campaign_desc = campaign_section
                for amt in amount_matches:
                    campaign_desc = campaign_desc.replace(amt, ' ')
                
                # Clean up the description
                campaign_desc = re.sub(r'\d{4}-\d{2}-\d{2}', ' ', campaign_desc)
                campaign_desc = re.sub(r'\s+', ' ', campaign_desc).strip()
                
                # Remove trailing date fragments
                campaign_desc = re.sub(r'\s*~?\s*\d{4}-\d{2}-\s*$', '', campaign_desc)
                
                record = {
                    "source_filename": filename,
                    "platform": "TikTok",
                    "invoice_type": "AP",
                    "invoice_id": base_fields.get("invoice_id"),
                    "line_number": i + 1,
                    "agency": "pk",
                    "project_id": None,
                    "project_name": None,
                    "objective": None,
                    "period": None,
                    "campaign_id": None,
                    "total": amount,
                    "description": campaign_desc,
                }
                
                # Extract details from campaign description
                extract_tiktok_details_fixed(campaign_desc, record)
                
                records.append(record)
    
    return records

def parse_tiktok_non_ap_fixed(text_content: str, filename: str, base_fields: dict) -> list:
    """Parse TikTok Non-AP invoice"""
    records = []
    
    # Find consumption details section
    consumption_start = text_content.find('Consumption Details:')
    if consumption_start == -1:
        return records
    
    consumption_text = text_content[consumption_start:]
    
    # Use regex to find all ST patterns with their associated data
    st_pattern = re.compile(r'(ST\d{10,})')
    
    # Find all ST occurrences
    st_matches = list(st_pattern.finditer(consumption_text))
    
    for i, match in enumerate(st_matches):
        st_id = match.group(1)
        start_pos = match.end()
        
        # Find the end position (next ST or end of text)
        if i + 1 < len(st_matches):
            end_pos = st_matches[i + 1].start()
        else:
            end_pos = len(consumption_text)
        
        # Extract the section for this ST
        section = consumption_text[start_pos:end_pos]
        
        # For non-AP, the campaign name doesn't have pk|
        # Extract everything until we hit amounts or dates
        lines = section.split('\n')
        campaign_parts = []
        amount = None
        
        for line in lines:
            line = line.strip()
            
            # Check if this is an amount
            if re.match(r'^[\d,]+\.\d{2}$', line):
                # Found an amount - check if it's the final amount
                amount_value = float(line.replace(',', ''))
                # Look for pattern of amounts (total, voucher, cash)
                amount = amount_value  # Use the last amount found
            elif re.match(r'^\d{4}-\d{2}-', line):
                # Date pattern, stop collecting campaign name
                break
            elif line and not line.startswith('TH') and not line.startswith('Country'):
                # Add to campaign name
                campaign_parts.append(line)
        
        if campaign_parts and amount:
            campaign_name = ' '.join(campaign_parts)
            
            record = {
                "source_filename": filename,
                "platform": "TikTok",
                "invoice_type": "Non-AP",
                "invoice_id": base_fields.get("invoice_id"),
                "line_number": i + 1,
                "agency": None,
                "project_id": None,
                "project_name": campaign_name,
                "objective": None,
                "period": None,
                "campaign_id": None,
                "total": amount,
                "description": campaign_name,
            }
            
            # Try to extract period from campaign name
            period_match = re.search(r'(Q[1-4]Y\d{2}|[A-Z][a-z]{2}\d{2})', campaign_name)
            if period_match:
                record['period'] = period_match.group(1)
            
            # Extract objective if present
            objectives = ['awareness', 'view', 'traffic', 'conversion', 'engagement', 'leadad']
            for obj in objectives:
                if obj.lower() in campaign_name.lower():
                    record['objective'] = obj.capitalize()
                    break
            
            records.append(record)
    
    return records

def extract_tiktok_details_fixed(description: str, record: dict):
    """Extract details from TikTok campaign description"""
    
    # Pattern: pk|[project_id|]details[ST]|campaign_id
    parts = description.split('|')
    
    if len(parts) >= 2:
        # Check if parts[1] looks like a project ID
        potential_id = parts[1].strip()
        
        if re.match(r'^\d+$', potential_id) or re.match(r'^[A-Z]+\d+$', potential_id):
            # Has project ID
            record['project_id'] = potential_id
            details_part = parts[2] if len(parts) > 2 else ''
        else:
            # No project ID, details start at parts[1]
            details_part = parts[1]
        
        # Extract campaign ID (last part after [ST])
        if '[ST]' in description:
            after_st = description.split('[ST]')[1]
            if '|' in after_st:
                record['campaign_id'] = after_st.split('|')[1].strip()
        
        # Parse details part
        if details_part:
            # Remove [ST] suffix if present
            details_part = details_part.replace('[ST]', '').strip()
            
            # Split by underscore
            detail_parts = details_part.split('_')
            
            project_parts = []
            for part in detail_parts:
                # Check for objective
                if part.lower() in ['awareness', 'view', 'traffic', 'conversion', 'engagement', 'leadad']:
                    record['objective'] = part.capitalize()
                    continue
                
                # Check for period
                if re.match(r'.*\d{2}$', part) and len(part) <= 10:
                    if any(month in part.upper() for month in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']):
                        record['period'] = part
                        continue
                    elif re.match(r'Q[1-4]Y\d{2}', part):
                        record['period'] = part
                        continue
                
                # Skip common keywords
                if part.lower() in ['pk', 'th', 'none', 'tiktok', 'boostpost', 'vdo', 'cta']:
                    continue
                
                # Add to project name
                if len(part) > 2:
                    project_parts.append(part)
            
            if project_parts:
                record['project_name'] = ' '.join(project_parts[:3])

def test_fixed_parser():
    """Test the fixed parser"""
    
    invoice_dir = "Invoice for testing"
    tiktok_files = [f for f in os.listdir(invoice_dir) if f.startswith('THTT') and f.endswith('.pdf')]
    tiktok_files.sort()
    
    total_amount = 0
    success_files = 0
    failed_files = []
    
    print(f"Testing fixed TikTok parser on {len(tiktok_files)} files...")
    
    for filename in tiktok_files:
        file_path = os.path.join(invoice_dir, filename)
        invoice_number = filename.replace('-Prakit Holdings Public Company Limited-Invoice.pdf', '')
        
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                text_content = ''.join([page.extract_text() for page in reader.pages])
            
            records = parse_tiktok_invoice_fixed(text_content, filename)
            if records:
                file_total = sum(r['total'] for r in records if r['total'])
                total_amount += file_total
                success_files += 1
                print(f"[OK] {invoice_number}: {file_total:,.2f} THB ({len(records)} lines)")
            else:
                failed_files.append(invoice_number)
                print(f"[FAIL] {invoice_number}: No records parsed")
            
        except Exception as e:
            print(f'[ERROR] {invoice_number}: Error - {e}')
            failed_files.append(invoice_number)
    
    print(f'\n{"="*80}')
    print(f'Successfully processed: {success_files}/{len(tiktok_files)} files')
    print(f'Total amount: {total_amount:,.2f} THB')
    print(f'Expected: 2,440,716.88 THB')
    print(f'Difference: {abs(total_amount - 2440716.88):,.2f} THB')
    
    if failed_files:
        print(f'\nFailed files ({len(failed_files)}):')
        for f in failed_files:
            print(f'  - {f}')

if __name__ == "__main__":
    test_fixed_parser()