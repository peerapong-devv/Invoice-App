#!/usr/bin/env python3
"""
Test script to analyze the 4 problematic AP files with large validation differences
"""

import os
import sys
import json
import fitz  # PyMuPDF

# Add backend directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the current parser logic from app.py
def create_final_unified_template():
    return {
        "source_filename": None, "platform": None, "invoice_type": None,
        "invoice_id": None, "line_number": None, "agency": None,
        "project_id": None, "project_name": None, "objective": None,
        "period": None, "campaign_id": None, "total": None, "description": None,
    }

def parse_invoice_text(text_content: str, filename: str):
    """Use the same logic as app.py"""
    if "tiktok" in text_content.lower() or "bytedance" in text_content.lower():
        platform = "TikTok"
        from final_tiktok_parser import parse_tiktok_invoice_final
        records = parse_tiktok_invoice_final(text_content, filename)
        for record in records:
            template = create_final_unified_template()
            template.update(record)
            record.clear()
            record.update(template)
        return records
    elif "google" in text_content.lower() and "ads" in text_content.lower():
        platform = "Google"
        # Use Google parser logic from app.py
        return parse_google_text(text_content, filename, platform)
    elif "facebook" in text_content.lower() or "meta" in text_content.lower():
        platform = "Facebook"
        return parse_facebook_text(text_content, filename, platform)
    else:
        return [{**create_final_unified_template(), "source_filename": filename, "platform": "Unknown"}]

def parse_google_text(text_content: str, filename: str, platform: str):
    """Enhanced Google invoice parser from app.py"""
    
    # First check if this might be a credit note
    try:
        from enhanced_credit_note_parser import parse_google_credit_note_enhanced, validate_credit_note_totals
        
        credit_keywords = ["กิจกรรมที่ไม่ถูกต้อง", "credit note", "ใบลดหนี้", "คืนเงิน", "-฿"]
        has_credit_keywords = any(keyword in text_content.lower() for keyword in credit_keywords)
        
        if has_credit_keywords:
            print(f"[DEBUG] {filename} might be a credit note, trying enhanced credit note parser")
            records = parse_google_credit_note_enhanced(text_content, filename)
            
            if records:
                validation = validate_credit_note_totals(records)
                print(f"[DEBUG] Credit note parser validation: {validation['message']}")
                
                for record in records:
                    template = create_final_unified_template()
                    template["invoice_total"] = None
                    template["item_type"] = None
                    template.update(record)
                    record.clear()
                    record.update(template)
                
                return records
        
    except Exception as e:
        print(f"[DEBUG] Credit note parser error: {e}, falling back to regular parser")
    
    # Special handling for 5298528895.pdf
    if '5298528895' in filename:
        try:
            from specific_google_parser_5298528895 import parse_google_invoice_5298528895
            return parse_google_invoice_5298528895(text_content, filename)
        except:
            pass
    
    # Try the enhanced parser first
    try:
        from fixed_google_parser_5298528895 import parse_google_invoice_fixed, validate_enhanced_totals
        
        records = parse_google_invoice_fixed(text_content, filename)
        validation = validate_enhanced_totals(records)
        print(f"[DEBUG] Enhanced parser validation: {validation['message']}")
        
        if records and validation.get('invoice_total'):
            print(f"[DEBUG] Using enhanced parser: {len(records)} records, total: {validation['invoice_total']}")
        else:
            print("[DEBUG] Enhanced parser failed, falling back to original parser")
            from perfect_google_parser import parse_google_invoice_perfect, validate_perfect_totals
            
            records = parse_google_invoice_perfect(text_content, filename)
            validation = validate_perfect_totals(records)
            print(f"[DEBUG] Original parser validation: {validation['message']}")
        
    except Exception as e:
        print(f"[DEBUG] Enhanced parser error: {e}, falling back to original parser")
        try:
            from perfect_google_parser import parse_google_invoice_perfect, validate_perfect_totals
            
            records = parse_google_invoice_perfect(text_content, filename)
            validation = validate_perfect_totals(records)
            print(f"[DEBUG] Original parser validation: {validation['message']}")
        except Exception as e2:
            print(f"[DEBUG] All parsers failed: {e2}")
            records = []
    
    # Debug output
    refunds = [r for r in records if r.get('item_type') == 'Refund']
    campaigns = [r for r in records if r.get('item_type') == 'Campaign']
    fees = [r for r in records if r.get('item_type') == 'Fee']
    
    print(f"[DEBUG] Found: {len(campaigns)} campaigns, {len(refunds)} refunds, {len(fees)} fees")
    
    # Ensure all records have required fields from template
    for record in records:
        template = create_final_unified_template()
        template["invoice_total"] = None
        template["item_type"] = None
        
        template.update(record)
        record.clear()
        record.update(template)
    
    return records

def parse_facebook_text(text_content: str, filename: str, platform: str):
    """Facebook parser from app.py"""
    import re
    
    def get_base_fields(text_content: str):
        base_data = {}
        match = re.search(r"(?:Invoice number|Invoice No\.|Invoice #:|หมายเลขใบแจ้งหนี้:)\s*([\w-]+)", text_content, re.IGNORECASE)
        if match:
            base_data["invoice_id"] = match.group(1).strip()
        return base_data
    
    base_fields = get_base_fields(text_content)
    records = []

    # Determine if this is AP invoice
    is_ap_invoice = "[ST]" in text_content
    invoice_type = "AP" if is_ap_invoice else "Non-AP"
    print(f"[DEBUG] File: {filename}, Detected invoice_type: {invoice_type}")

    if is_ap_invoice:
        records = parse_ap_invoice_by_lines(text_content, filename, base_fields)
    else:
        records = parse_non_ap_invoice(text_content, filename, base_fields)

    return records

def parse_ap_invoice_by_lines(text_content: str, filename: str, base_fields: dict) -> list:
    """Parse AP invoice by following Line# structure exactly"""
    import re
    
    records = []
    lines = text_content.split('\n')
    
    current_item = None
    line_items = []
    skip_next_amount = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Check for subtotal/total markers to skip their amounts
        if line in ['Subtotal:', 'Invoice Total:', 'Freight:', 'VAT @0%:']:
            skip_next_amount = True
            i += 1
            continue
        
        # Check if this is a line number (1-3 digits only)
        if line.isdigit() and len(line) <= 3:
            line_number = int(line)
            
            # Save previous item if exists
            if current_item:
                line_items.append(current_item)
            
            # Start new item
            current_item = {
                'line_number': line_number,
                'description_lines': [],
                'amount': None,
                'has_st': False
            }
            skip_next_amount = False
            
        elif current_item is not None:
            # Check if this line is a pure amount (like "1,234.56")
            amount_match = re.match(r'^[\d,.-]+\.\d{2}$', line)
            if amount_match and not skip_next_amount:
                current_item['amount'] = float(line.replace(',', ''))
            elif amount_match and skip_next_amount:
                skip_next_amount = False
            else:
                # Add to description
                current_item['description_lines'].append(line)
                if '[ST]' in line:
                    current_item['has_st'] = True
        else:
            # Handle amounts without current_item
            amount_match = re.match(r'^[\d,.-]+\.\d{2}$', line)
            if amount_match and skip_next_amount:
                skip_next_amount = False
        
        i += 1
    
    # Don't forget the last item
    if current_item:
        line_items.append(current_item)
    
    print(f"[DEBUG] Found {len(line_items)} line items in {filename}")
    
    # Convert to records
    for item in line_items:
        # Only process items with [ST] marker for AP invoices
        if not item['has_st']:
            print(f"[DEBUG] Skipping Line {item['line_number']}: No [ST] marker")
            continue
        
        # Combine description lines
        full_description = ' '.join(item['description_lines']).strip()
        
        record = create_final_unified_template()
        record.update(base_fields)
        record.update({
            "source_filename": filename,
            "platform": "Facebook",
            "invoice_type": "AP",
            "line_number": item['line_number'],
            "description": full_description,
            "total": item['amount'],
            "agency": "pk",
        })
        
        # Enhanced pattern matching for project details
        extract_project_details_enhanced(full_description, record)
        
        records.append(record)
        try:
            print(f"[DEBUG] AP Line {item['line_number']}: Amount: {item['amount']}")
        except UnicodeEncodeError:
            print(f"[DEBUG] AP Line {item['line_number']}: [Unicode] Amount: {item['amount']}")
    
    return records

def extract_project_details_enhanced(description: str, record: dict):
    """Extract project details using enhanced patterns"""
    import re
    
    # Main AP pattern: pk|project|details[ST]|campaign
    main_pattern = r'pk\|([^|]*)\|([^[]*)\[ST\]\|([^|\s]+)'
    match = re.search(main_pattern, description, re.IGNORECASE)
    
    if match:
        project_id = match.group(1).strip()
        complex_part = match.group(2).strip()
        campaign_id = match.group(3).strip()
        
        record['project_id'] = project_id if project_id != 'none' else None
        record['campaign_id'] = campaign_id
        
        # Parse complex middle part
        parse_complex_details_enhanced(complex_part, record)

def parse_complex_details_enhanced(complex_part: str, record: dict):
    """Parse the complex middle section between pk| and [ST]"""
    import re
    
    if not complex_part:
        return
    
    # Clean up the complex part
    parts = [p.strip() for p in complex_part.split('_') if p.strip()]
    
    # Extract project type and name
    project_name_parts = []
    found_objective = False
    
    for part in parts:
        # Stop at objective keywords
        if part.lower() in ['awareness', 'conversion', 'traffic', 'leadad', 'reach', 'engagement']:
            record['objective'] = part.capitalize()
            found_objective = True
            continue
        
        # Skip common metadata
        if part.lower() in ['pk', 'th', 'none', 'facebook', 'cta', 'vdo', 'combine']:
            continue
        
        # Skip format codes (all caps with numbers)
        if re.match(r'^[A-Z]{2,}[0-9Q]+', part):
            continue
        
        # Skip if we've found objective and this looks like a period
        if found_objective and re.match(r'.*[0-9]{2,}', part):
            record['period'] = part
            continue
        
        # Add to project name if it looks like a meaningful part
        if not found_objective and len(part) > 1:
            project_name_parts.append(part)
    
    # Set project name
    if project_name_parts:
        record['project_name'] = '-'.join(project_name_parts)
    
    # Extract period if not found above
    if not record.get('period'):
        period_patterns = [
            r'(Q[1-4]Y\d{2})',
            r'([A-Z]{3,4}Y?\d{2})',
            r'(\d{1,2}-?\w{3}-?\d{2,4})',
        ]
        
        for pattern in period_patterns:
            period_match = re.search(pattern, complex_part)
            if period_match:
                record['period'] = period_match.group(1)
                break

def parse_non_ap_invoice(text_content: str, filename: str, base_fields: dict) -> list:
    """Parse Facebook Non-AP invoice using Line# structure after ar@meta.com"""
    import re
    
    records = []
    lines = text_content.split('\n')
    
    # Find the start point after payment details
    start_extraction = False
    line_items = []
    current_item = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Start looking for line items after ar@meta.com
        if "ar@meta.com" in line:
            start_extraction = True
            i += 1
            continue
            
        if start_extraction:
            # Check if this is a line number (single digit)
            if re.match(r'^\d+$', line):
                # Save previous item if exists
                if current_item:
                    line_items.append(current_item)
                
                # Start new item
                current_item = {
                    'line_number': int(line),
                    'description_lines': [],
                    'amount': None
                }
                
            elif current_item is not None:
                # Check if this line is an amount (like "1,234.56 ")
                amount_match = re.match(r'^[\d,]+\.\d{2}\s*$', line)
                if amount_match:
                    current_item['amount'] = float(line.replace(',', '').strip())
                else:
                    # Add to description
                    current_item['description_lines'].append(line)
        
        i += 1
    
    # Don't forget the last item
    if current_item:
        line_items.append(current_item)
    
    print(f"[DEBUG] Found {len(line_items)} non-AP line items in {filename}")
    
    # Convert to records
    for item in line_items:
        # Combine description lines
        full_description = ' '.join(item['description_lines']).strip()
        
        # Skip if no description or amount
        if not full_description or item['amount'] is None:
            continue
        
        record = create_final_unified_template()
        record.update(base_fields)
        record.update({
            "source_filename": filename,
            "platform": "Facebook",
            "invoice_type": "Non-AP",
            "line_number": item['line_number'],
            "description": full_description,
            "total": item['amount'],
        })
        records.append(record)
    
    return records

def test_file(filename):
    """Test parsing a single file"""
    file_path = os.path.join("Invoice for testing", filename)
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"Testing: {filename}")
    print(f"{'='*60}")
    
    try:
        # Extract text
        with fitz.open(file_path) as doc:
            full_text = "\n".join(page.get_text() for page in doc)
        
        if not full_text:
            print("No text extracted!")
            return
        
        print(f"Text length: {len(full_text)} characters")
        
        # Parse using current logic
        records = parse_invoice_text(full_text, filename)
        
        print(f"Parsed {len(records)} records")
        
        # Calculate total
        total_amount = 0
        for record in records:
            if record.get('total'):
                total_amount += record['total']
        
        print(f"Total parsed amount: {total_amount:,.2f} THB")
        
        # Show first few lines of text for debugging
        print(f"\nFirst 500 characters of text:")
        print(repr(full_text[:500]))
        
        # Show records summary
        print(f"\nRecords summary:")
        for i, record in enumerate(records[:5]):  # Show first 5 records
            print(f"  Record {i+1}: Line {record.get('line_number')}, Amount: {record.get('total')}, Platform: {record.get('platform')}")
            if record.get('description'):
                print(f"    Description: {record['description'][:100]}...")
        
        if len(records) > 5:
            print(f"  ... and {len(records)-5} more records")
        
        return records, total_amount, full_text
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        import traceback
        traceback.print_exc()
        return None, 0, ""

def main():
    """Test the 4 problematic files"""
    
    problem_files = [
        "5297830454.pdf",  # diff: 1,774 THB
        "5298134610.pdf",  # diff: 1,400 THB
        "5298157309.pdf",  # diff: 1,898 THB  
        "5298361576.pdf"   # diff: 968 THB
    ]
    
    results = {}
    
    for filename in problem_files:
        records, total_amount, full_text = test_file(filename)
        results[filename] = {
            'records': records,
            'total_amount': total_amount,
            'full_text': full_text[:1000] if full_text else ""  # First 1000 chars for analysis
        }
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for filename in problem_files:
        result = results[filename]
        if result['records']:
            print(f"{filename}: {len(result['records'])} records, Total: {result['total_amount']:,.2f} THB")
        else:
            print(f"{filename}: Failed to parse")
    
    # Save results for analysis
    with open('problem_files_analysis.json', 'w', encoding='utf-8') as f:
        # Make records JSON serializable
        serializable_results = {}
        for filename, result in results.items():
            serializable_results[filename] = {
                'total_amount': result['total_amount'],
                'record_count': len(result['records']) if result['records'] else 0,
                'full_text_preview': result['full_text']
            }
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed analysis saved to: problem_files_analysis.json")

if __name__ == "__main__":
    main()