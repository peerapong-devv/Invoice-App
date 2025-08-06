import re

# Test the exact data from Record 4
section_data = '''ST1150054104
AP -HOME x 
725811693493
183333765765029
pk|40077|SDH_pk_th-
TH
2025-06-
8,000.00
0.00
8,000.00

57
Prakit
4347778
0
single-detached-house-
moden-bangna-
theparak_none_Traffic_
VDO_TTTRAFFICQ2Y25
_[ST]|2089P47
01 ~ 
2025-06-
30
Subtotal before'''

print("=== Testing Campaign Description Extraction ===")

# Try to extract using whole-section approach
pk_start = section_data.find('pk|')
if pk_start >= 0:
    pk_section = section_data[pk_start:]
    
    # Find all lines that could be part of campaign description
    lines = pk_section.split('\n')
    print("All lines after pk|:")
    for i, line in enumerate(lines):
        print(f"  {i}: {repr(line.strip())}")
    
    # Try pattern matching for the complete description
    # Based on debug, we should get:
    # pk|40077|SDH_pk_th-single-detached-house-moden-bangna-theparak_none_Traffic_VDO_TTTRAFFICQ2Y25_[ST]|2089P47
    
    # Extract campaign parts using regex patterns
    campaign_lines = []
    found_pk = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('pk|'):
            campaign_lines.append(line)
            found_pk = True
            continue
            
        if found_pk:
            # Add lines that contain campaign content indicators
            if any(indicator in line.lower() for indicator in ['single-detached', 'house', 'bangna', 'traffic', 'vdo', '_[st]']):
                campaign_lines.append(line)
            elif line == 'Subtotal before':
                break
    
    result = ' '.join(campaign_lines)
    print(f"\nExtracted: {result}")
    
    # Also try regex to find the complete pattern
    # Pattern should match: pk|project_id|details_[ST]|campaign_id
    full_pattern = r'pk\|[^|]*\|[^[]*\[ST\]\|[^|\s]+'
    full_match = re.search(full_pattern, section_data.replace('\n', ' '), re.DOTALL)
    if full_match:
        print(f"Regex match: {full_match.group(0)}")