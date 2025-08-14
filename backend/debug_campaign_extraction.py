#!/usr/bin/env python3
"""Debug campaign ID extraction"""

import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Test cases with full descriptions
test_cases = [
    {
        'desc': "(฿) p k | 4 0 1 0 9 | S D H _ p k _ t h - s i n g l e - d e t a c h e d - h o u s e - c e n t r o - r a t c h a p r u e k - 3 _ n o n e _ T r a f f i c _ R e s p o n s i v e _ G D N Q 2 Y 2 5 _ [ S T ] | 2 0 8 9 P 1 2 50277 การคลิก 18,550.72",
        'expected_campaign': '2089P12'
    },
    {
        'desc': "p k | 7 0 0 9 2 | A p i t o w n _ p k _ t h - u p c o u n t r y - p r o j e c t s - a p i t o w n - u d o n t h a n i _ n o n e _ T r a f f i c _ R e s p o n s i v e _ [ S T ] | 2 1 0 0 P 0 2 2529",
        'expected_campaign': '2100P02'
    },
    {
        'desc': "p k | 2 0 0 5 7 | A p i t o w n _ p k _ t h - u p c o u n t r y - p r o j e c t s - a p i t o w n - r a t c h a b u r i _ n o n e _ T r a f f i c _ S e a r c h _ G e n e r i c _ [ S T ] | 2 0 7 7 P 0 1 253",
        'expected_campaign': '2077P01'
    }
]

print("DEBUGGING CAMPAIGN EXTRACTION")
print("="*80)

for test in test_cases:
    desc = test['desc']
    expected = test['expected_campaign']
    
    # Clean
    clean = desc.replace(' ', '')
    
    print(f"\nDescription: {desc[:80]}...")
    print(f"Expected campaign: {expected}")
    print(f"Cleaned: {clean}")
    
    # Try different patterns
    patterns = [
        (r'\|(\d{4}P\d{2})', 'After pipe'),
        (r'(\d{4}P\d{2})', 'Anywhere'),
        (r'\[ST\]\|(\d{4}P\d+)', 'After [ST]|'),
        (r'_([A-Z0-9]+)_\[ST\]', 'Before [ST]'),
        (r'_(\w+)การคลิก', 'Before การคลิก')
    ]
    
    found = False
    for pattern, name in patterns:
        match = re.search(pattern, clean)
        if match:
            print(f"  {name}: {match.group(1)}")
            if match.group(1) == expected:
                found = True
                print(f"  ✓ CORRECT!")
                break
    
    if not found:
        # Try manual extraction
        print(f"  Manual check:")
        # Find [ST]| and get what's after
        if '[ST]|' in clean:
            idx = clean.find('[ST]|')
            after_st = clean[idx+5:idx+15]
            print(f"    After [ST]|: {after_st}")
        
        # Find pattern XXXXPXX
        import re
        campaign_match = re.findall(r'\d{4}P\d{2}', clean)
        if campaign_match:
            print(f"    All campaign patterns found: {campaign_match}")
    
    print("-"*60)