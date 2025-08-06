#!/usr/bin/env python3

import re
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from enhanced_tiktok_line_parser import parse_campaign_name_components

def show_campaign_parsing_details():
    """Show exactly what the campaign parsing function expects vs actual data"""
    
    print("=" * 80)
    print("CAMPAIGN NAME PARSING ANALYSIS")
    print("=" * 80)
    
    print("\n1. WHAT THE PARSER EXPECTS:")
    print("-" * 40)
    expected_format = "pk|CD_pk_60029|CD_pk_th-condominium-rhythm-ekkamai-estate_none_Traffic_tiktok_VDO_TTQ2Y25-JUN25-APCD-NO2_[ST]|1972P04"
    print(f"Format: {expected_format}")
    
    print("\nExpected parsing logic:")
    print("  1. Split by '|' -> ['pk', 'CD_pk_60029', 'CD_pk_th-condominium-rhythm-ekkamai-estate_none_Traffic_tiktok_VDO_TTQ2Y25-JUN25-APCD-NO2_[ST]', '1972P04']")
    print("  2. Project ID from parts[1]: 'CD_pk_60029' -> extract number '60029'")
    print("  3. Project Name from parts[2]: 'CD_pk_th-condominium-rhythm-ekkamai-estate_none_Traffic' -> 'th condominium rhythm ekkamai estate'")
    print("  4. Objective from parts[2]: '_none_Traffic_' -> 'Traffic'")
    
    # Test with expected format
    components = parse_campaign_name_components(expected_format)
    print(f"\nResult with expected format: {components}")
    
    print("\n2. WHAT WE ACTUALLY HAVE:")
    print("-" * 40)
    actual_campaigns = [
        "ARABUS Chilled Cup Q2Y25 Lucky Draw Campaign_Traffic_Jun25_4,200 Clicks_28,560 THB",
        "ARABUS Chilled Cup Q2Y25 Lucky Draw Campaign_Traffic_Jun25_Pointx2_946 Clicks_7,571 THB"
    ]
    
    for i, campaign in enumerate(actual_campaigns, 1):
        print(f"Campaign {i}: {campaign}")
        
        print(f"\nSplit by '|': {campaign.split('|')}")
        print("  -> Only 1 part, no pipe separators!")
        
        components = parse_campaign_name_components(campaign)
        print(f"  -> Parser result: {components}")
        print()
    
    print("\n3. MANUAL EXTRACTION FROM ACTUAL FORMAT:")
    print("-" * 40)
    
    for i, campaign in enumerate(actual_campaigns, 1):
        print(f"Campaign {i}: {campaign}")
        
        # Try to extract meaningful info
        project_name_match = re.search(r'^([A-Z]+[^_]+)', campaign)
        project_name = project_name_match.group(1).strip() if project_name_match else 'Unknown'
        
        objective_match = re.search(r'Campaign_([^_]+)', campaign)
        objective = objective_match.group(1) if objective_match else 'Unknown'
        
        # Could extract project ID from other sources or generate
        project_id = 'ARABUS_Q2Y25'  # Could be derived
        
        print(f"  Manually extracted:")
        print(f"    Project Name: {project_name}")
        print(f"    Objective: {objective}")
        print(f"    Project ID: {project_id}")
        print()
    
    print("\n4. THE CURRENT PARSING FUNCTION CODE:")
    print("-" * 40)
    print("""
def parse_campaign_name_components(campaign_name):
    components = {
        'project_id': 'Unknown',
        'project_name': 'Unknown', 
        'objective': 'Unknown'
    }
    
    if not campaign_name or campaign_name == 'Unknown Campaign':
        return components
    
    # Split by pipes  <-- PROBLEM: No pipes in our data!
    parts = campaign_name.split('|')
    
    if len(parts) >= 2:
        # Project ID from second part <-- PROBLEM: parts[1] doesn't exist!
        project_id_raw = parts[1]
        # Extract numeric part from CD_pk_60029 format
        project_id_match = re.search(r'(\\d+)$', project_id_raw)
        # ... rest of logic never executes
    """)
    
    print("\n5. WHY EXTRACTION FAILS:")
    print("-" * 40)
    print("✗ campaign_name.split('|') returns only 1 element (no pipes)")
    print("✗ len(parts) >= 2 is False, so project ID extraction skipped")
    print("✗ len(parts) >= 3 is False, so project name/objective extraction skipped")
    print("✗ All components remain 'Unknown'")
    
    print("\n6. REQUIRED FIX:")
    print("-" * 40)
    print("Need to add fallback logic for non-pipe formats:")
    print("1. Check if campaign contains '|' - if yes, use existing logic")
    print("2. If no pipes, use alternative parsing for descriptive format")
    print("3. Extract project name from beginning of string")
    print("4. Extract objective from 'Campaign_[objective]' pattern")
    print("5. Generate or derive project ID from available data")

if __name__ == "__main__":
    show_campaign_parsing_details()