import re

def parse_tiktok_invoice(text_content: str, filename: str):
    """
    Corrected TikTok invoice parser that handles the specific PDF text extraction issues
    found in THTT202502215532 and THTT202502215554
    """
    
    # Clean up text
    text_content = text_content.replace('\u200b', '')
    
    # Extract base fields
    base_fields = {}
    invoice_match = re.search(r"Invoice No\.\s*([\w-]+)", text_content, re.IGNORECASE)
    if invoice_match:
        base_fields["invoice_id"] = invoice_match.group(1).strip()
    
    records = []
    
    # Check if this is an AP invoice - must have BOTH ST pattern AND pk| pattern
    has_st_pattern = bool(re.search(r'ST\d{10,}', text_content))
    has_pk_pattern = bool(re.search(r'pk\|', text_content))
    is_ap = has_st_pattern and has_pk_pattern
    
    if is_ap:
        records = parse_tiktok_ap_corrected(text_content, filename, base_fields)
    else:
        records = parse_tiktok_non_ap_corrected(text_content, filename, base_fields)
    
    return records

def parse_tiktok_ap_corrected(text_content: str, filename: str, base_fields: dict) -> list:
    """Parse TikTok AP invoice with corrected logic for PDF text extraction issues"""
    records = []
    
    # Find consumption details section
    consumption_start = text_content.find('Consumption Details:')
    if consumption_start == -1:
        return records
    
    consumption_text = text_content[consumption_start:]
    lines = consumption_text.split('\n')
    
    print(f"Processing AP invoice with {len(lines)} lines")
    
    # Look for pk| patterns that may be concatenated with other data
    i = 0
    line_number = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for pk| pattern - may be concatenated with campaign ID
        pk_match = re.search(r'(\d*)pk\|([^|]*\|[^|]*)', line)
        if pk_match:
            # Extract the campaign description starting from pk|
            pk_start = line.find('pk|')
            line_after_pk = line[pk_start:]
            
            print(f"\nFound pk| pattern at line {i}: {line[:100]}...")
            print(f"  Extracted pk| part: {line_after_pk[:100]}...")
            
            # Collect multi-line campaign description
            campaign_parts = [line_after_pk]
            j = i + 1
            
            # Continue collecting until we find [ST] or reach amount pattern
            st_found = False
            while j < len(lines) and not st_found:
                next_line = lines[j].strip()
                
                # Check if this line contains [ST] - end of campaign description
                if '[ST]' in next_line:
                    campaign_parts.append(next_line)
                    st_found = True
                    break
                
                # Check if this line has amount pattern (means we've gone too far)
                if re.search(r'[\d,]+\.\d{2}', next_line):
                    break
                
                # Add non-empty lines to campaign description
                if next_line and not re.match(r'^\d{4}-\d{2}-', next_line):
                    campaign_parts.append(next_line)
                
                j += 1
            
            # Join campaign description
            campaign_desc = ''.join(campaign_parts)
            print(f"  Full campaign description: {campaign_desc[:150]}...")
            
            # Look for amounts - they might be in the same line or nearby
            amount = None
            
            # Look for amounts in the original line and subsequent lines
            search_lines = [line] + lines[j:j+5]  # Include current line and next 5
            all_amounts = []
            
            for search_line in search_lines:
                line_amounts = re.findall(r'[\d,]+\.\d{2}', search_line)
                all_amounts.extend(line_amounts)
            
            if len(all_amounts) >= 3:
                # Pattern: total, voucher (0.00), cash - use cash (3rd amount)
                amount = float(all_amounts[2].replace(',', ''))
                print(f"  Found 3+ amounts: {all_amounts} -> using cash amount: {amount}")
            elif len(all_amounts) >= 1:
                # Use the last amount found
                amount = float(all_amounts[-1].replace(',', ''))
                print(f"  Found amounts: {all_amounts} -> using last: {amount}")
            
            # If no amount found in normal way, look for amount pattern specifically
            if not amount:
                # Look for the pattern where amounts are at the end of lines after dates
                for k in range(j, min(j + 10, len(lines))):
                    search_line = lines[k].strip()
                    # Look for date followed by amounts
                    if re.search(r'2025-\d{2}-\d{2}', search_line):
                        # Check the next few lines for amounts
                        for m in range(k, min(k + 3, len(lines))):
                            amt_line = lines[m].strip()
                            amt_matches = re.findall(r'[\d,]+\.\d{2}', amt_line)
                            if len(amt_matches) >= 3:
                                amount = float(amt_matches[2].replace(',', ''))
                                print(f"  Found amount after date: {amt_matches} -> using {amount}")
                                break
                        if amount:
                            break
            
            if amount and amount > 0:
                line_number += 1
                print(f"  Created record {line_number} with amount: {amount}")
                
                # Extract campaign_id from [ST] pattern
                campaign_id = None
                if '[ST]' in campaign_desc:
                    st_split = campaign_desc.split('[ST]')
                    if len(st_split) > 1:
                        after_st = st_split[1]
                        if after_st.startswith('|'):
                            after_st = after_st[1:]
                        # Extract campaign ID (remove non-alphanumeric at end)
                        campaign_id = re.sub(r'[^\w]+.*$', '', after_st.strip())
                        if campaign_id:
                            print(f"    Extracted campaign_id: {campaign_id}")
                
                # Extract project_id from the pk| pattern
                project_id = None
                pk_parts = campaign_desc.split('|')
                if len(pk_parts) >= 2:
                    potential_id = pk_parts[1]
                    if re.match(r'^\d+$', potential_id) or re.match(r'^[A-Z0-9]+$', potential_id):
                        project_id = potential_id
                        print(f"    Extracted project_id: {project_id}")
                
                record = {
                    "source_filename": filename,
                    "platform": "TikTok",
                    "invoice_type": "AP",
                    "invoice_id": base_fields.get("invoice_id"),
                    "line_number": line_number,
                    "agency": "pk",
                    "project_id": project_id,
                    "project_name": None,
                    "objective": None,
                    "period": None,
                    "campaign_id": campaign_id,
                    "total": amount,
                    "description": campaign_desc,
                }
                
                # Extract additional details
                extract_ap_details(campaign_desc, record)
                
                records.append(record)
            
            i = j
        else:
            i += 1
    
    return records

def parse_tiktok_non_ap_corrected(text_content: str, filename: str, base_fields: dict) -> list:
    """Parse TikTok Non-AP invoice with corrected logic for PDF text extraction issues"""
    records = []
    
    print(f"Processing Non-AP invoice")
    
    # Find consumption details section
    consumption_start = text_content.find('Consumption Details:')
    if consumption_start == -1:
        return records
    
    consumption_text = text_content[consumption_start:]
    lines = consumption_text.split('\n')
    
    # For Non-AP, look for campaign content after ST patterns
    # The structure is different - no pk| pattern but has campaign descriptions
    
    i = 0
    line_number = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for ST pattern
        if re.match(r'^ST\d{10,}$', line):
            st_id = line
            print(f"\nFound ST pattern at line {i}: {st_id}")
            
            # Look for campaign description in the following lines
            j = i + 1
            campaign_lines = []
            amount = None
            
            # Skip header-like lines and collect campaign description
            while j < len(lines):
                current = lines[j].strip()
                
                # Stop if we hit another ST pattern
                if re.match(r'^ST\d{10,}$', current):
                    break
                
                # Look for amount pattern (might be merged like 2,000.000.002,000.00)
                amount_matches = re.findall(r'[\d,]+\.\d{2}', current)
                if len(amount_matches) >= 3:
                    # Use the 3rd amount (cash consumption)
                    amount = float(amount_matches[2].replace(',', ''))
                    print(f"  Found amount pattern: {amount_matches} -> using {amount}")
                    break
                elif amount_matches and len(amount_matches) == 1:
                    # Single amount might be the total
                    amount = float(amount_matches[0].replace(',', ''))
                    print(f"  Found single amount: {amount}")
                    break
                
                # Skip obvious header lines
                if current and not re.match(r'^\d+$', current) and 'HOSPITAL' not in current:
                    # This might be part of campaign description
                    if len(current) > 5 and not re.match(r'^\d{4}-\d{2}-', current):
                        campaign_lines.append(current)
                        current_safe = current.encode('ascii', errors='replace').decode('ascii')
                        print(f"    Added to campaign: {current_safe[:50]}...")
                
                j += 1
            
            # Create record if we have campaign info and amount
            if campaign_lines and amount and amount > 0:
                line_number += 1
                
                # Join campaign description
                campaign_desc = ' '.join(campaign_lines)
                # Safe print for campaign description
                campaign_desc_safe = campaign_desc.encode('ascii', errors='replace').decode('ascii')
                print(f"  Created Non-AP record {line_number}: {amount} - {campaign_desc_safe[:100]}...")
                
                record = {
                    "source_filename": filename,
                    "platform": "TikTok",
                    "invoice_type": "Non-AP",
                    "invoice_id": base_fields.get("invoice_id"),
                    "line_number": line_number,
                    "agency": None,
                    "project_id": None,
                    "project_name": None,
                    "objective": None,
                    "period": None,
                    "campaign_id": None,
                    "total": amount,
                    "description": campaign_desc,
                }
                
                # Extract some basic details
                extract_non_ap_details(campaign_desc, record)
                
                records.append(record)
            
            i = j
        else:
            i += 1
    
    return records

def extract_ap_details(description: str, record: dict):
    """Extract details from AP campaign description"""
    
    # Parse the pk| structure for project details
    parts = description.split('|')
    
    if len(parts) >= 3:
        # Extract details from the main description part
        main_desc = parts[2] if len(parts) > 2 else parts[1]
        
        # Remove [ST] and everything after
        if '[ST]' in main_desc:
            main_desc = main_desc.split('[ST]')[0]
        
        # Parse details from underscore-separated parts
        detail_parts = main_desc.split('_')
        
        project_parts = []
        for part in detail_parts:
            part = part.strip()
            
            # Check for objective
            if part.lower() in ['view', 'awareness', 'traffic', 'conversion', 'engagement']:
                record['objective'] = part.capitalize()
                continue
            
            # Check for period patterns
            if re.match(r'.*Y\d{2}', part) or re.match(r'.*\d{2}', part):
                if any(month in part.upper() for month in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']):
                    record['period'] = part
                    continue
            
            # Skip common keywords
            if part.lower() in ['pk', 'th', 'none', 'tiktok', 'boostpost', 'vdo']:
                continue
            
            # Add to project name
            if len(part) > 2:
                project_parts.append(part)
        
        if project_parts:
            record['project_name'] = ' '.join(project_parts[:2])  # Take first 2 parts

def extract_non_ap_details(description: str, record: dict):
    """Extract details from Non-AP campaign description"""
    
    # Extract objective if present
    objectives = ['View', 'Community', 'Traffic', 'Conversion', 'Awareness', 'Engagement', 'Reach']
    for obj in objectives:
        if obj in description:
            record['objective'] = obj
            break
    
    # Extract period from date patterns
    period_match = re.search(r'(\d{1,2}-\d{1,2}[A-Za-z]{3})', description)
    if period_match:
        record['period'] = period_match.group(1)
    
    # Extract project name (first meaningful word)
    words = description.split()
    for word in words:
        if len(word) > 3 and word.lower() not in ['content', 'reach', 'kids']:
            record['project_name'] = word
            break

# Test the corrected parser
if __name__ == "__main__":
    # Test with problematic content from debug
    test_ap = """
    Invoice No. THTT202502215554
    Consumption Details:
    7pk|SDH_pk_40065_th-single-detached-house-centro-vibhavadi_none_View_tiktok_Boostpost_FBViewY25-JUN25-SDH-31_[ST]|1359G01TH 2025-06-11 ~248,324.390.008,324.39
    """
    
    test_non_ap = """
    Invoice No. THTT202502215532
    Consumption Details:
    ST1150054052
    87RJR HOSPITAL720468587096
    XXX-0625 - RJR AWO'25
    | 11-18Jun | 
    Jun_Ad1_Kids content 
    | Reach | 2,000THB 
    2,000.000.002,000.00
    """
    
    print("Testing corrected AP parser:")
    ap_results = parse_tiktok_invoice(test_ap, "test_ap.pdf")
    for r in ap_results:
        print(f"  Line {r['line_number']}: {r['total']} - {r['description'][:100]}...")
    
    print("\nTesting corrected Non-AP parser:")
    non_ap_results = parse_tiktok_invoice(test_non_ap, "test_non_ap.pdf")
    for r in non_ap_results:
        print(f"  Line {r['line_number']}: {r['total']} - {r['description'][:100]}...")