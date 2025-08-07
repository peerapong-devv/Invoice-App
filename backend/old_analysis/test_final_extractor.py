#!/usr/bin/env python3
"""Test the final Google extractor"""

import os
import sys
import fitz

sys.stdout.reconfigure(encoding='utf-8')

# Test direct import first
try:
    from google_final_extractor import parse_google_invoice
    print("✓ Successfully imported google_final_extractor")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

def test_file(filename):
    """Test extraction on a specific file"""
    filepath = os.path.join('..', 'Invoice for testing', filename)
    
    print(f"\n{'='*80}")
    print(f"Testing: {filename}")
    print('='*80)
    
    # Read text
    with fitz.open(filepath) as doc:
        text_content = ""
        for page in doc:
            text_content += page.get_text()
    
    # Parse
    try:
        items = parse_google_invoice(text_content, filename)
        
        print(f"Extracted {len(items)} items:")
        
        total = 0
        for item in items:
            desc = item['description'][:60] + '...' if len(item['description']) > 60 else item['description']
            print(f"\n{item['line_number']}. {desc}")
            print(f"   Amount: {item['amount']:,.2f}")
            print(f"   Type: {item['invoice_type']}")
            
            total += item['amount']
        
        print(f"\nTotal: {total:,.2f}")
        
        return len(items), total
        
    except Exception as e:
        print(f"✗ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

# Test key files
test_files = [
    '5297692778.pdf',  # Should have 3-4 items
    '5297692787.pdf',  # Should have 8+ items
    '5300624442.pdf',  # Should have 6+ items
]

for file in test_files:
    test_file(file)