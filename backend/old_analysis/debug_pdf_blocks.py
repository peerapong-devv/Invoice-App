#!/usr/bin/env python3
"""Debug PDF block extraction"""

import os
import sys
import fitz

sys.stdout.reconfigure(encoding='utf-8')

def debug_blocks(filename):
    """Debug block extraction"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Debugging: {filename}")
    print('='*80)
    
    with fitz.open(filepath) as doc:
        if len(doc) < 2:
            print("No page 2!")
            return
        
        page = doc[1]
        blocks = page.get_text("blocks")
        
        print(f"Total blocks on page 2: {len(blocks)}")
        
        # Find blocks with campaign indicators
        campaign_blocks = []
        for i, block in enumerate(blocks):
            text = str(block[4]).strip()
            if any(indicator in text for indicator in ['DMCRM', 'DMHEALTH', 'DMHealth', 'pk|', '|']):
                campaign_blocks.append((i, block))
        
        print(f"\nFound {len(campaign_blocks)} blocks with campaign indicators:")
        
        for idx, (i, block) in enumerate(campaign_blocks[:10]):
            x0, y0, x1, y1, text = block[:5]
            print(f"\nBlock {i} (Y: {y0:.1f}):")
            print(f"  Text: {text.strip()[:100]}...")

# Test different files
for file in ['5297692778.pdf', '5300624442.pdf']:
    debug_blocks(file)