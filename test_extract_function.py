import sys
sys.path.append('backend')
from final_tiktok_parser import extract_campaign_description

# Test data from problematic section
test_section = '''ST1150054104
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

# Find pk section
pk_start = test_section.find('pk|')
if pk_start >= 0:
    pk_section = test_section[pk_start:]
    result = extract_campaign_description(pk_section)
    print(f"Function result: {result}")
    print(f"Length: {len(result)}")
else:
    print("No pk| found")