#!/usr/bin/env python3
"""
Learn from TikTok parser success to fix Facebook AP parser
"""

import fitz
import re
from truly_fixed_facebook_parser import parse_facebook_invoice_truly_fixed
from final_improved_tiktok_parser_v2 import parse_ap_campaign_pattern_v2

def analyze_facebook_ap_patterns():
    """Analyze Facebook AP invoice patterns"""
    
    print("="*80)
    print("ANALYZING FACEBOOK AP PATTERNS")
    print("="*80)
    
    # Test Facebook AP invoice 246543739.pdf
    filename = "246543739.pdf"
    filepath = f"../Invoice for testing/{filename}"
    
    with fitz.open(filepath) as doc:
        text = ''
        for page in doc:
            text += page.get_text()
    
    # Count [ST] patterns
    st_patterns = re.findall(r'([^[]+\[ST\]\|[A-Z0-9]+)', text)
    
    print(f"\nFile: {filename}")
    print(f"Total [ST] patterns found: {len(st_patterns)}")
    
    # Show first 10 patterns
    print("\nFirst 10 [ST] patterns:")
    for i, pattern in enumerate(st_patterns[:10], 1):
        # Clean up the pattern
        pattern = pattern.strip()
        pattern = re.sub(r'\s+', ' ', pattern)
        
        print(f"\n{i}. Raw pattern:")
        print(f"   {pattern[:100]}..." if len(pattern) > 100 else f"   {pattern}")
        
        # Check if it has pk| prefix
        if 'pk|' in pattern:
            print("   [OK] Has pk| prefix")
            
            # Try to parse like TikTok
            tiktok_result = parse_ap_campaign_pattern_v2(pattern)
            print(f"   TikTok parser result:")
            print(f"     - agency: {tiktok_result['agency']}")
            print(f"     - project_id: {tiktok_result['project_id']}")
            print(f"     - campaign_id: {tiktok_result['campaign_id']}")
        else:
            print("   [ERROR] No pk| prefix")
    
    # Extract amounts near [ST] patterns
    print("\n\nLooking for amounts near [ST] patterns:")
    
    # Find [ST] patterns with amounts
    pattern_with_amount = r'([^[]+\[ST\]\|[A-Z0-9]+)\s*([0-9,]+\.[0-9]{2})'
    matches = re.findall(pattern_with_amount, text)
    
    print(f"Found {len(matches)} [ST] patterns with amounts")
    
    total = 0
    for i, (pattern, amount) in enumerate(matches[:5], 1):
        pattern = pattern.strip()
        pattern = re.sub(r'\s+', ' ', pattern)
        amount_float = float(amount.replace(',', ''))
        total += amount_float
        
        print(f"\n{i}. Pattern: {pattern[:60]}...")
        print(f"   Amount: {amount} ({amount_float:,.2f})")
    
    print(f"\nTotal of first 5 items: {total:,.2f} THB")
    
    # Check invoice total
    total_match = re.search(r'Invoice\s+Total[:\s]*([0-9,]+\.[0-9]{2})', text)
    if total_match:
        invoice_total = float(total_match.group(1).replace(',', ''))
        print(f"\nInvoice Total: {invoice_total:,.2f} THB")

def compare_parsers():
    """Compare TikTok and Facebook AP parsing"""
    
    print("\n\n" + "="*80)
    print("COMPARING TIKTOK VS FACEBOOK AP PARSING")
    print("="*80)
    
    # Sample patterns
    tiktok_pattern = "pk|40022|SDH_pk_th-single-detached-house-centro-onnut-suvarnabhumi_none_Awareness_VDO_FBAWARENESSQ2Y25_[ST]|2089P22"
    facebook_pattern = "Instagram - pk|40022|SDH_pk_th-single-detached-house-centro-onnut-suvarnabhumi_none_Awareness_VDO_FBAWARENESSQ2Y25_[ST]|2089P22"
    
    print("\nTikTok pattern:")
    print(f"  {tiktok_pattern}")
    
    print("\nFacebook pattern:")
    print(f"  {facebook_pattern}")
    
    print("\nKey differences:")
    print("  1. Facebook has 'Instagram - ' prefix")
    print("  2. Otherwise the structure is IDENTICAL")
    print("  3. Both use: pk|project_id|details_[ST]|campaign_id")
    
    # Parse with TikTok parser
    tiktok_result = parse_ap_campaign_pattern_v2(tiktok_pattern)
    
    # Clean Facebook pattern and parse
    facebook_clean = facebook_pattern.replace('Instagram - ', '').replace('Facebook - ', '')
    facebook_result = parse_ap_campaign_pattern_v2(facebook_clean)
    
    print("\nParsing results:")
    print(f"  TikTok: project_id={tiktok_result['project_id']}, campaign_id={tiktok_result['campaign_id']}")
    print(f"  Facebook: project_id={facebook_result['project_id']}, campaign_id={facebook_result['campaign_id']}")

if __name__ == "__main__":
    analyze_facebook_ap_patterns()
    compare_parsers()