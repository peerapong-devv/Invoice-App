#!/usr/bin/env python3
"""Test AP field extraction"""

import sys
from google_parser_professional import extract_ap_fields_professional

sys.stdout.reconfigure(encoding='utf-8')

# Test cases
test_descriptions = [
    "(฿) p k | 4 0 1 0 9 | S D H _ p k _ t h - s i n g l e - d e t a c h e d - h o u s e - c e n t r o - r a t c h a p r u e k - 3 _ n o n e _ T r a f f i c _ R e s p o n s i v e _ G D N Q 2 Y 2 5 _ [ S T",
    "p k | 7 0 0 9 2 | A p i t o w n _ p k _ t h - u p c o u n t r y - p r o j e c t s - a p i t o w n - u d o n t h a n i _ n o n e _ T r a f f i c _ S e a r c h _ G e n e r i c _ [ S T ] | 2 1 0 0 P 0 2",
    "p k | 2 0 0 5 7 | A p i t o w n _ p k _ t h - u p c o u n t r y - p r o j e c t s - a p i t o w n - r a t c h a b u r i _ n o n e _ C o n v e r s i o n _ S e a r c h _ B r a n d _ [ S T ] | 2 0 7 7 P"
]

print("TESTING AP FIELD EXTRACTION")
print("="*80)

for desc in test_descriptions:
    print(f"\nOriginal: {desc[:80]}...")
    
    # Clean for display
    clean = desc.replace(' ', '')
    print(f"Cleaned: {clean[:80]}...")
    
    # Extract fields
    fields = extract_ap_fields_professional(desc)
    
    print("Extracted fields:")
    print(f"  Agency: {fields['agency']}")
    print(f"  Project ID: {fields['project_id']}")
    print(f"  Project Name: {fields['project_name']}")
    print(f"  Campaign ID: {fields['campaign_id']}")
    print(f"  Objective: {fields['objective']}")
    print("-"*60)