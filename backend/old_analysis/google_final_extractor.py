#!/usr/bin/env python3
"""
Google Final Extractor - Based on deep analysis of actual PDF structure
Handles the specific patterns found in Google invoices
"""

import fitz
import re
from typing import Dict, List, Any, Optional

def extract_google_invoice_final(pdf_path: str, filename: str) -> List[Dict[str, Any]]:
    """Final extractor based on actual PDF structure analysis"""
    
    doc = fitz.open(pdf_path)
    
    # Extract basic info
    invoice_number = extract_invoice_number(filename)
    base_info = {
        'platform': 'Google',
        'filename': filename,
        'invoice_number': invoice_number,
        'invoice_id': invoice_number
    }
    
    # Get all text content
    all_text = ""
    for page_num in range(len(doc)):
        all_text += doc[page_num].get_text() + "\n"
    
    doc.close()
    
    # Extract line items using the patterns we discovered
    items = []
    
    # Method 1: Extract main campaign items
    main_items = extract_main_campaign_items(all_text, base_info)
    items.extend(main_items)
    
    # Method 2: Extract credit adjustments
    credit_items = extract_credit_adjustments_final(all_text, base_info)
    items.extend(credit_items)
    
    # If no items found, create a single summary item
    if not items:
        total = extract_total_amount_final(all_text)
        if total != 0:
            items = [create_single_item(base_info, total, all_text)]
    
    # Set line numbers and invoice type
    invoice_type = determine_invoice_type_final(all_text, items)
    for i, item in enumerate(items):
        item['line_number'] = i + 1
        item['invoice_type'] = invoice_type
        if 'agency' not in item:
            item['agency'] = 'pk' if invoice_type == 'AP' else None
    
    return items

def extract_main_campaign_items(text: str, base_info: Dict) -> List[Dict[str, Any]]:
    """Extract main campaign items using the discovered patterns"""
    items = []
    
    # Pattern 1: Look for the specific structure we found:
    # - Campaign description (fragmented as individual characters)
    # - Followed by clicks amount
    # - Followed by "การคลิก" (clicks)
    # - Followed by monetary amount
    
    lines = text.split('\n')
    
    # Look for monetary amounts that are not totals or adjustments
    amounts_found = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Look for significant amounts (not totals, not small adjustments)
        amount_match = re.match(r'^(\d{1,3}(?:,\d{3})*\.\d{2})$', line)
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(',', ''))
                
                # Filter for campaign amounts (typically in range 1000-100000)
                if 1000 <= amount <= 100000:
                    
                    # Look for context clues around this amount
                    context_start = max(0, i - 20)
                    context_end = min(len(lines), i + 5)
                    context_lines = lines[context_start:context_end]
                    
                    # Look for "การคลิก" (clicks) which indicates a campaign line
                    if any('การคลิก' in ctx_line for ctx_line in context_lines):
                        
                        # Try to find clicks amount
                        clicks = extract_clicks_from_context(context_lines)
                        
                        # Try to reconstruct campaign description
                        description = reconstruct_campaign_description(context_lines, i - context_start)
                        
                        if description:
                            items.append({
                                **base_info,
                                'amount': amount,
                                'total': amount,
                                'description': description,
                                'agency': 'pk',
                                'project_id': extract_project_id_from_desc(description),
                                'project_name': extract_project_name_from_desc(description),
                                'objective': extract_objective_from_desc(description),
                                'period': None,
                                'campaign_id': extract_campaign_id_from_desc(description),
                                'clicks': clicks
                            })
                            
                            amounts_found.append(amount)
                        
            except ValueError:
                continue
    
    return items

def extract_clicks_from_context(context_lines: List[str]) -> Optional[int]:
    """Extract clicks amount from context"""
    
    for line in context_lines:
        line = line.strip()
        
        # Look for pure numeric lines that could be clicks (before "การคลิก")
        if re.match(r'^\d{1,7}$', line):
            try:
                clicks = int(line)
                # Reasonable range for clicks
                if 100 <= clicks <= 10000000:
                    return clicks
            except ValueError:
                continue
    
    return None

def reconstruct_campaign_description(context_lines: List[str], amount_index: int) -> Optional[str]:
    """Reconstruct campaign description from fragmented text"""
    
    # Look for campaign patterns in the context
    full_context = ' '.join(context_lines)
    
    # Pattern 1: Look for pk|projectId|description pattern
    pk_match = re.search(r'pk\|(\d+)\|([^|]+)', full_context)
    if pk_match:
        project_id = pk_match.group(1)
        description_part = pk_match.group(2)
        return f"pk|{project_id}|{description_part}"
    
    # Pattern 2: Look for fragmented campaign description
    # The fragmented text appears as individual characters like: p k | 4 0 1 0 9 | S D H ...
    # We need to reconstruct this
    
    # Find lines with single characters and try to reconstruct
    single_chars = []
    for line in context_lines:
        line = line.strip()
        if len(line) == 1 and (line.isalnum() or line in '|_-'):
            single_chars.append(line)
    
    if len(single_chars) > 10:  # Need reasonable length
        reconstructed = ''.join(single_chars)
        
        # Look for pk| pattern in reconstructed text
        if reconstructed.startswith('pk|'):
            # Clean up and extract meaningful parts
            parts = reconstructed.split('|')
            if len(parts) >= 3:
                project_id = parts[1] if parts[1].isdigit() else None
                description = parts[2] if len(parts) > 2 else "Campaign"
                
                # Clean description
                description = description.replace('_', ' ').title()
                
                return f"pk|{project_id}|{description}" if project_id else description
    
    # Pattern 3: Look for project name keywords in context
    project_keywords = ['SDH', 'Apitown', 'Parrot', 'Centro', 'Townhome', 'Condo']
    for keyword in project_keywords:
        if keyword.lower() in full_context.lower():
            return f"Google Ads - {keyword}"
    
    return "Google Ads Campaign"

def extract_credit_adjustments_final(text: str, base_info: Dict) -> List[Dict[str, Any]]:
    """Extract credit adjustments with the patterns we found"""
    items = []
    
    # Pattern: กิจกรรมที่ไม่ถูกต้อง followed by invoice numbers and amounts
    credit_pattern = r'กิจกรรมที่ไม่ถูกต้อง[^:]*?:\s*(\d{10})[^0-9]*?(-?\d{1,3}(?:,\d{3})*\.\d{2})'
    
    matches = re.finditer(credit_pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            original_invoice = match.group(1)
            amount_str = match.group(2)
            amount = float(amount_str.replace(',', ''))
            
            # Credit adjustments should be negative
            if amount > 0:
                amount = -amount
            
            items.append({
                **base_info,
                'amount': amount,
                'total': amount,
                'description': f'กิจกรรมที่ไม่ถูกต้อง - หมายเลขใบแจ้งหนี้เดิม: {original_invoice}',
                'agency': 'pk',
                'project_id': 'CREDIT',
                'project_name': 'Credit Adjustment',
                'objective': 'N/A',
                'period': None,
                'campaign_id': 'CREDIT'
            })
            
        except (ValueError, IndexError):
            continue
    
    # Also look for standalone negative amounts that might be credits
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if re.match(r'^-\d{1,3}(?:,\d{3})*\.\d{2}$', line):
            try:
                amount = float(line.replace(',', ''))
                if -1000 < amount < -1:  # Reasonable credit range
                    items.append({
                        **base_info,
                        'amount': amount,
                        'total': amount,
                        'description': 'Credit Adjustment',
                        'agency': 'pk',
                        'project_id': 'CREDIT',
                        'project_name': 'Credit Adjustment',
                        'objective': 'N/A',
                        'period': None,
                        'campaign_id': 'CREDIT'
                    })
            except ValueError:
                continue
    
    return items

def extract_total_amount_final(text: str) -> float:
    """Extract total amount from invoice"""
    
    # Look for total patterns
    patterns = [
        r'฿(\d{1,3}(?:,\d{3})*\.\d{2})',  # Thai baht symbol
        r'ยอดรวม[^0-9]*?(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'Total[^0-9]*?(\d{1,3}(?:,\d{3})*\.\d{2})',
    ]
    
    largest_amount = 0.0
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                amount = float(match.group(1).replace(',', ''))
                if abs(amount) > abs(largest_amount):
                    largest_amount = amount
            except ValueError:
                continue
    
    return largest_amount

def determine_invoice_type_final(text: str, items: List[Dict]) -> str:
    """Determine if invoice is AP or Non-AP"""
    
    # Check items for AP indicators
    has_campaigns = any('pk|' in item.get('description', '') for item in items)
    has_clicks = 'การคลิก' in text  # Direct check instead of any()
    has_credits = any(item.get('project_id') == 'CREDIT' for item in items)
    
    # If has campaigns or clicks, it's AP
    if has_campaigns or has_clicks:
        return 'AP'
    
    # If only credits, could be Non-AP
    if has_credits and not has_campaigns:
        return 'Non-AP'
    
    # Default to AP for Google invoices
    return 'AP'

def create_single_item(base_info: Dict, total: float, text: str) -> Dict[str, Any]:
    """Create single item when detailed extraction fails"""
    
    # Extract account name
    account_match = re.search(r'บัญชี:\s*([^\n]+)', text)
    account_name = account_match.group(1).strip() if account_match else 'Google Ads'
    
    # Extract period
    period = extract_period_final(text)
    
    return {
        **base_info,
        'amount': total,
        'total': total,
        'description': f'{account_name}' + (f' - {period}' if period else ''),
        'agency': None,
        'project_id': None,
        'project_name': None,
        'objective': None,
        'period': period,
        'campaign_id': None
    }

def extract_period_final(text: str) -> Optional[str]:
    """Extract billing period"""
    
    # Thai date pattern
    thai_match = re.search(r'(\d{1,2}\s+\S+\s+\d{4})\s*[-–]\s*(\d{1,2}\s+\S+\s+\d{4})', text)
    if thai_match:
        return f"{thai_match.group(1)} - {thai_match.group(2)}"
    
    return None

def extract_invoice_number(filename: str) -> str:
    """Extract invoice number from filename"""
    match = re.search(r'(\d{10})', filename)
    return match.group(1) if match else 'Unknown'

def extract_project_id_from_desc(description: str) -> Optional[str]:
    """Extract project ID"""
    match = re.search(r'pk\|(\d+)', description)
    return match.group(1) if match else None

def extract_project_name_from_desc(description: str) -> Optional[str]:
    """Extract project name"""
    desc_lower = description.lower()
    
    if 'sdh' in desc_lower:
        return 'Single Detached House'
    elif 'apitown' in desc_lower:
        return 'Apitown'
    elif 'parrot' in desc_lower:
        return 'Parrot'
    elif 'centro' in desc_lower or 'ratchapruek' in desc_lower:
        return 'Centro Ratchapruek'
    elif 'townhome' in desc_lower:
        return 'Townhome'
    
    return 'Google Ads Campaign'

def extract_objective_from_desc(description: str) -> Optional[str]:
    """Extract objective"""
    desc_lower = description.lower()
    
    if 'responsive' in desc_lower:
        return 'Traffic - Responsive'
    elif 'search' in desc_lower:
        if 'generic' in desc_lower:
            return 'Search - Generic'
        elif 'brand' in desc_lower:
            return 'Search - Brand'
        elif 'compet' in desc_lower:
            return 'Search - Competitor'
        else:
            return 'Search'
    elif 'traffic' in desc_lower:
        return 'Traffic'
    elif 'leadad' in desc_lower:
        return 'Lead Generation'
    
    return 'Traffic'

def extract_campaign_id_from_desc(description: str) -> Optional[str]:
    """Extract campaign ID"""
    # Look for patterns like 2089P12, GDNQ2Y25, etc.
    match = re.search(r'\b([A-Z0-9]{6,})\b', description)
    return match.group(1) if match else None

def test_final_extractor():
    """Test the final extractor"""
    
    base_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    test_files = [
        ("5297692778.pdf", "Expected: 4 items (1 main campaign + 2 credits)"),
        ("5297692787.pdf", "Expected: 13 items"),
        ("5300624442.pdf", "Expected: multiple items")
    ]
    
    for filename, expected in test_files:
        pdf_path = f"{base_path}\\{filename}"
        
        print(f"\n{'='*80}")
        print(f"TESTING FINAL EXTRACTOR: {filename}")
        print(f"{expected}")
        print(f"{'='*80}")
        
        try:
            items = extract_google_invoice_final(pdf_path, filename)
            
            print(f"\nExtracted {len(items)} line items:")
            
            total_amount = 0
            for item in items:
                amount = item['amount']
                total_amount += amount
                description = item['description'][:60]
                project_name = item.get('project_name', 'N/A')
                clicks = item.get('clicks', 'N/A')
                
                print(f"  Line {item['line_number']}: ")
                print(f"    Amount: {amount:>12,.2f}")
                print(f"    Description: {description}...")
                print(f"    Project: {project_name}")
                print(f"    Clicks: {clicks}")
                print()
            
            print(f"Total amount: {total_amount:>12,.2f}")
            print(f"Invoice type: {items[0]['invoice_type'] if items else 'N/A'}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("Google Final Extractor - Based on Deep Analysis")
    print("=" * 60)
    
    test_final_extractor()