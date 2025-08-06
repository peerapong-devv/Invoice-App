#!/usr/bin/env python3

import PyPDF2
import re
import sys
import os

# Add backend to path to import the parser
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from enhanced_tiktok_line_parser import (
    parse_tiktok_invoice_detailed,
    extract_consumption_section,
    parse_tiktok_consumption_table,
    process_tiktok_table_row,
    extract_campaign_name_from_row,
    parse_campaign_name_components
)

def debug_tiktok_parser(pdf_path):
    """Debug the TikTok parser to understand why it's failing"""
    
    print("=" * 80)
    print(f"DEBUGGING TIKTOK PARSER FOR: {os.path.basename(pdf_path)}")
    print("=" * 80)
    
    # Extract text from PDF
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        full_text = "\n".join(page.extract_text() for page in pdf_reader.pages)
    
    print("\n1. RAW PDF TEXT EXTRACTION:")
    print("-" * 40)
    lines = full_text.split('\n')
    for i, line in enumerate(lines, 1):
        if line.strip():
            print(f"{i:3d}: {line}")
    
    # Extract consumption section
    consumption_section = extract_consumption_section(lines)
    
    print("\n2. CONSUMPTION SECTION EXTRACTION:")
    print("-" * 40)
    if consumption_section:
        print(f"Found {len(consumption_section)} lines in consumption section:")
        for i, line in enumerate(consumption_section, 1):
            print(f"{i:3d}: {line}")
    else:
        print("No consumption section found!")
    
    # Parse table data
    if consumption_section:
        table_data = parse_tiktok_consumption_table(consumption_section)
        
        print("\n3. TABLE DATA PARSING:")
        print("-" * 40)
        if table_data:
            print(f"Found {len(table_data)} table rows:")
            for i, row in enumerate(table_data, 1):
                print(f"\nRow {i}:")
                for key, value in row.items():
                    print(f"  {key}: {value}")
        else:
            print("No table data extracted!")
    
    # Test campaign name extraction manually
    print("\n4. MANUAL CAMPAIGN NAME ANALYSIS:")
    print("-" * 40)
    
    # Look for campaign names in the text
    campaign_patterns = [
        r'ARABUS[^T]+Traffic[^T]+',
        r'pk\|[^|]+\|[^|]+',
        r'Campaign_Traffic_[^T]+',
        r'Q2Y25[^T]+THB'
    ]
    
    for pattern in campaign_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            print(f"Pattern '{pattern}' found:")
            for match in matches:
                print(f"  {match}")
    
    # Extract actual campaign names from the PDF
    print("\n5. ACTUAL CAMPAIGN NAMES FROM PDF:")
    print("-" * 40)
    
    # Look for the actual campaign names in the consumption details
    campaign_lines = []
    in_consumption = False
    
    for line in lines:
        if 'Consumption Details:' in line:
            in_consumption = True
            continue
        
        if in_consumption and ('ARABUS' in line or 'Campaign' in line or 'Traffic' in line):
            campaign_lines.append(line.strip())
    
    print("Campaign-related lines found:")
    for line in campaign_lines:
        print(f"  {line}")
    
    # Test the actual parser
    print("\n6. RUNNING ACTUAL PARSER:")
    print("-" * 40)
    
    records = parse_tiktok_invoice_detailed(full_text, os.path.basename(pdf_path))
    
    if records:
        print(f"Parser returned {len(records)} records:")
        for i, record in enumerate(records, 1):
            print(f"\nRecord {i}:")
            print(f"  Agency: {record.get('agency', 'N/A')}")
            print(f"  Project ID: {record.get('project_id', 'N/A')}")
            print(f"  Project Name: {record.get('project_name', 'N/A')}")
            print(f"  Objective: {record.get('objective', 'N/A')}")
            print(f"  Campaign ID: {record.get('campaign_id', 'N/A')}")
            print(f"  Campaign Name: {record.get('campaign_name', 'N/A')}")
            print(f"  Amount: {record.get('amount', 0):,.2f}")
    else:
        print("Parser returned no records!")
    
    # Test specific functions with manual data
    print("\n7. TESTING PARSE_CAMPAIGN_NAME_COMPONENTS FUNCTION:")
    print("-" * 40)
    
    # Test with sample campaign names we can see in the PDF
    test_campaigns = [
        "ARABUS Chilled Cup Q2Y25 Lucky Draw Campaign_Traffic_Jun25_4,200 Clicks_28,560 THB",
        "ARABUS Chilled Cup Q2Y25 Lucky Draw Campaign_Traffic_Jun25_Pointx2_946 Clicks_7,571 THB"
    ]
    
    for campaign in test_campaigns:
        print(f"\nTesting campaign: {campaign}")
        components = parse_campaign_name_components(campaign)
        print(f"  Parsed components: {components}")
    
    return records

def analyze_why_parsing_fails():
    """Analyze why the parsing is failing for this specific invoice"""
    
    print("\n" + "=" * 80)
    print("ANALYSIS: WHY THE PARSING IS FAILING")
    print("=" * 80)
    
    print("\n1. ISSUE IDENTIFICATION:")
    print("   The TikTok parser is designed for invoices with pk| patterns in campaign names")
    print("   This invoice (THTT202502215482) has different campaign name format:")
    print("   - Expected: pk|CD_pk_60029|CD_pk_th-condominium-rhythm-ekkamai-estate_none_Traffic_tiktok")
    print("   - Actual: ARABUS Chilled Cup Q2Y25 Lucky Draw Campaign_Traffic_Jun25")
    
    print("\n2. PARSER ASSUMPTIONS:")
    print("   - extract_campaign_name_from_row() looks for 'pk|' pattern")
    print("   - parse_campaign_name_components() expects pipe-separated format")
    print("   - This invoice uses a completely different naming convention")
    
    print("\n3. INVOICE TYPE:")
    print("   - This appears to be a Non-AP invoice (simple advertiser name: 'DM - Arabus')")
    print("   - But it has Consumption Details, so parser treats it as AP")
    print("   - The campaign names don't follow AP project naming conventions")
    
    print("\n4. SOLUTIONS NEEDED:")
    print("   - Handle Non-AP invoices with consumption details differently")
    print("   - Add fallback parsing for campaign names without pk| patterns")
    print("   - Extract project info from different campaign name formats")

if __name__ == "__main__":
    pdf_path = r"Invoice for testing\THTT202502215482-Prakit Holdings Public Company Limited-Invoice.pdf"
    
    if os.path.exists(pdf_path):
        records = debug_tiktok_parser(pdf_path)
        analyze_why_parsing_fails()
    else:
        print(f"File not found: {pdf_path}")