#!/usr/bin/env python3
"""
Extract exact line items from all Google invoices to create hardcoded patterns
This will analyze all 54 Google files and extract every campaign, credit, and fee item
"""

import os
import re
import json
import PyPDF2
from typing import Dict, List, Any
from decimal import Decimal

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def parse_google_line_items_exact(text_content: str, filename: str) -> Dict[str, Any]:
    """
    Parse Google invoice to extract EXACT line items:
    - Campaign lines with pk| patterns
    - Credit adjustments (กิจกรรมที่ไม่ถูกต้อง)
    - Regulatory fees (ค่าธรรมเนียม)
    - All amounts and descriptions
    """
    
    result = {
        "filename": filename,
        "invoice_id": filename.replace('.pdf', ''),
        "total_amount": 0.0,
        "line_items": [],
        "campaign_items": [],
        "credit_items": [],
        "fee_items": [],
        "invoice_type": "Unknown"
    }
    
    lines = text_content.split('\n')
    
    # Extract invoice ID and total
    invoice_match = re.search(r'หมายเลขใบแจ้งหนี้:\s*(\d+)', text_content)
    if invoice_match:
        result["invoice_id"] = invoice_match.group(1)
    
    # Extract total amount
    total_patterns = [
        r'จำนวนเงินรวมที่ต้องชำระในสกุลเงิน\s+THB\s*฿?([-\d,]+\.?\d*)',
        r'ยอดรวมในสกุลเงิน\s+THB\s*฿?([-\d,]+\.?\d*)',
    ]
    
    for pattern in total_patterns:
        total_match = re.search(pattern, text_content)
        if total_match:
            try:
                amount_str = total_match.group(1).replace(',', '')
                result["total_amount"] = float(amount_str)
                break
            except:
                pass
    
    # Determine if AP or Non-AP
    has_pk = 'pk|' in text_content
    result["invoice_type"] = "AP" if has_pk else "Non-AP"
    
    if has_pk:
        # Extract AP campaigns - look for table structure
        result.update(_extract_ap_campaigns(text_content))
        result.update(_extract_credit_adjustments(text_content))
        result.update(_extract_regulatory_fees(text_content))
    
    return result

def _extract_ap_campaigns(text_content: str) -> Dict[str, Any]:
    """Extract campaign line items from AP invoices"""
    campaigns = []
    lines = text_content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for pk| patterns
        if 'pk|' in line:
            pk_match = re.search(r'(pk\|[^\s]+)', line)
            if pk_match:
                campaign_code = pk_match.group(1)
                
                # Look for amount and clicks in the same line or next few lines
                amount = None
                clicks = None
                unit = None
                
                # Check current line for amount
                amount_match = re.search(r'([\d,]+\.?\d*)\s*$', line)
                if amount_match:
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                    except:
                        pass
                
                # Look in next few lines
                j = i + 1
                while j < min(i + 5, len(lines)) and amount is None:
                    next_line = lines[j].strip()
                    
                    # Look for clicks and amount pattern: "25297 การคลิก 9,895.90"
                    click_pattern = r'(\d+)\s+(การคลิก|clicks?)\s+([\d,]+\.?\d*)'
                    click_match = re.match(click_pattern, next_line)
                    if click_match:
                        clicks = int(click_match.group(1))
                        unit = click_match.group(2)
                        amount = float(click_match.group(3).replace(',', ''))
                        break
                    
                    # Look for standalone amount
                    amount_match = re.match(r'^([\d,]+\.?\d*)\s*$', next_line)
                    if amount_match:
                        try:
                            amount = float(amount_match.group(1).replace(',', ''))
                            break
                        except:
                            pass
                    
                    j += 1
                
                if amount is not None and amount > 0:
                    campaign_item = {
                        "campaign_code": campaign_code,
                        "amount": amount,
                        "clicks": clicks,
                        "unit": unit,
                        "line_index": i
                    }
                    campaigns.append(campaign_item)
        
        i += 1
    
    return {"campaign_items": campaigns}

def _extract_credit_adjustments(text_content: str) -> Dict[str, Any]:
    """Extract credit adjustment items (negative amounts)"""
    credits = []
    lines = text_content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for credit adjustment patterns
        if 'กิจกรรมที่ไม่ถูกต้อง' in line or 'Invalid activity' in line:
            # Extract description
            description = line
            
            # Look for amount in next few lines
            amount = None
            j = i + 1
            while j < min(i + 5, len(lines)):
                next_line = lines[j].strip()
                
                # Look for negative amount
                neg_match = re.match(r'^-?([\d,]+\.?\d*)\s*$', next_line)
                if neg_match:
                    try:
                        amount = -abs(float(neg_match.group(1).replace(',', '')))
                        break
                    except:
                        pass
                j += 1
            
            if amount is not None:
                credit_item = {
                    "description": description,
                    "amount": amount,
                    "line_index": i
                }
                credits.append(credit_item)
        
        # Also look for standalone negative amounts
        elif re.match(r'^-[\d,]+\.?\d*\s*$', line):
            try:
                amount = float(line.replace(',', ''))
                if amount < 0:
                    credit_item = {
                        "description": "Credit adjustment",
                        "amount": amount,
                        "line_index": i
                    }
                    credits.append(credit_item)
            except:
                pass
        
        i += 1
    
    return {"credit_items": credits}

def _extract_regulatory_fees(text_content: str) -> Dict[str, Any]:
    """Extract regulatory fees"""
    fees = []
    lines = text_content.split('\n')
    
    # Look for regulatory fee patterns
    fee_patterns = [
        r'ค่าธรรมเนียมในการดำเนินงานตามกฎระเบียบของประเทศสเปน\s*\*?\s*([\d,]+\.?\d*)',
        r'ค่าธรรมเนียมในการดำเนินงานตามกฎระเบียบของประเทศฝรั่งเศส\s*\*?\s*([\d,]+\.?\d*)',
        r'ค่าธรรมเนียมในการดำเนินงานตามกฏระเบียบของประเทศฝรั่งเศส\s*\*?\s*([\d,]+\.?\d*)',
    ]
    
    for i, line in enumerate(lines):
        for pattern in fee_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    fee_type = "Spain" if "สเปน" in line else "France"
                    
                    fee_item = {
                        "description": line.strip(),
                        "fee_type": fee_type,
                        "amount": amount,
                        "line_index": i
                    }
                    fees.append(fee_item)
                except:
                    pass
    
    return {"fee_items": fees}

def analyze_all_google_files():
    """Analyze all Google invoice files and extract exact patterns"""
    
    # Find all Google files (starting with 5)
    invoice_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    google_files = []
    
    for filename in os.listdir(invoice_dir):
        if filename.startswith('5') and filename.endswith('.pdf'):
            google_files.append(filename)
    
    google_files.sort()
    print(f"Found {len(google_files)} Google invoice files")
    
    all_results = {
        "metadata": {
            "total_files": len(google_files),
            "analysis_date": "2025-08-06",
            "purpose": "Extract exact line items for hardcoded patterns"
        },
        "files": {}
    }
    
    for filename in google_files:
        print(f"Processing {filename}...")
        pdf_path = os.path.join(invoice_dir, filename)
        
        # Extract text
        text_content = extract_text_from_pdf(pdf_path)
        if not text_content:
            continue
        
        # Parse exact line items
        result = parse_google_line_items_exact(text_content, filename)
        all_results["files"][filename] = result
        
        # Print summary
        campaign_count = len(result.get("campaign_items", []))
        credit_count = len(result.get("credit_items", []))
        fee_count = len(result.get("fee_items", []))
        total_amount = result.get("total_amount", 0)
        
        print(f"  Total: {total_amount:,.2f} THB")
        print(f"  Campaigns: {campaign_count}, Credits: {credit_count}, Fees: {fee_count}")
        print()
    
    # Save results
    output_file = "google_exact_line_items_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"Analysis complete! Results saved to {output_file}")
    
    # Generate summary statistics
    generate_summary_stats(all_results)

def generate_summary_stats(results: Dict):
    """Generate summary statistics"""
    
    total_files = len(results["files"])
    ap_files = 0
    non_ap_files = 0
    total_campaigns = 0
    total_credits = 0
    total_fees = 0
    total_amount = 0
    
    print("\n" + "="*50)
    print("SUMMARY STATISTICS")
    print("="*50)
    
    for filename, data in results["files"].items():
        if data["invoice_type"] == "AP":
            ap_files += 1
        else:
            non_ap_files += 1
        
        total_campaigns += len(data.get("campaign_items", []))
        total_credits += len(data.get("credit_items", []))
        total_fees += len(data.get("fee_items", []))
        total_amount += data.get("total_amount", 0)
    
    print(f"Total Files: {total_files}")
    print(f"AP Files: {ap_files}")
    print(f"Non-AP Files: {non_ap_files}")
    print(f"Total Campaign Items: {total_campaigns}")
    print(f"Total Credit Items: {total_credits}")
    print(f"Total Fee Items: {total_fees}")
    print(f"Total Amount: {total_amount:,.2f} THB")
    print()
    
    # Files with most line items
    print("FILES WITH MOST LINE ITEMS:")
    file_items = []
    for filename, data in results["files"].items():
        total_items = len(data.get("campaign_items", [])) + len(data.get("credit_items", [])) + len(data.get("fee_items", []))
        file_items.append((filename, total_items, data.get("total_amount", 0)))
    
    file_items.sort(key=lambda x: x[1], reverse=True)
    for filename, item_count, amount in file_items[:10]:
        print(f"  {filename}: {item_count} items, {amount:,.2f} THB")

if __name__ == "__main__":
    analyze_all_google_files()