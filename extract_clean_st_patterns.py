import sys
import re
import os
import shutil
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'C:\Users\peerapong\invoice-reader-app\backend')
from app import process_invoice_file

def clean_description(desc):
    """Clean description to extract just the core pattern"""
    if not desc:
        return desc
    
    # Remove the numerical data and extra text after [ST]
    # Pattern: everything up to [ST]|campaign_id
    pattern = r'^(.*?)\[ST\]\|([A-Z0-9]+)'
    match = re.search(pattern, desc)
    if match:
        main_part = match.group(1).strip()
        campaign_id = match.group(2)
        return f"{main_part}[ST]|{campaign_id}"
    
    return desc.strip()

INVOICE_DIR = r'C:\Users\peerapong\invoice-reader-app\Invoice for testing'
UPLOAD_FOLDER = r'C:\Users\peerapong\invoice-reader-app\backend\uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ap_filenames = [
    '246543739.pdf',
    '246546622.pdf', 
    '246578231.pdf',
    '246579423.pdf',
    '246727587.pdf',
    '246738919.pdf',
    '246774670.pdf',
    '246791975.pdf',
    '246865374.pdf'
]

print("=== COMPREHENSIVE [ST] LINE ITEM ANALYSIS ===\n")

all_clean_patterns = []
invoice_counts = {}

for file_name in ap_filenames:
    file_path = os.path.join(INVOICE_DIR, file_name)
    if os.path.exists(file_path):
        dest_path = os.path.join(UPLOAD_FOLDER, file_name)
        shutil.copy(file_path, dest_path)
        
        processed_data = process_invoice_file(dest_path, file_name)
        
        st_count = 0
        if processed_data:
            for record in processed_data:
                if record.get('description') and '[ST]' in record.get('description'):
                    cleaned = clean_description(record.get('description'))
                    all_clean_patterns.append(cleaned)
                    st_count += 1
        
        invoice_counts[file_name] = st_count
        print(f"{file_name}: {st_count} [ST] items")
        
        if os.path.exists(dest_path):
            os.remove(dest_path)

print(f"\n=== SUMMARY ===")
print(f"Total invoices processed: {len(ap_filenames)}")
print(f"Total [ST] line items found: {len(all_clean_patterns)}")

# Show breakdown by invoice
print(f"\nBreakdown by invoice:")
for invoice, count in invoice_counts.items():
    print(f"  {invoice}: {count}")

# Extract unique patterns for analysis
unique_patterns = list(set(all_clean_patterns))
print(f"\nUnique [ST] patterns: {len(unique_patterns)}")

# Categorize patterns
print(f"\n=== PATTERN CATEGORIES ===")

# 1. Project type patterns
print("\n1. PROJECT TYPES FOUND:")
project_types = set()
for pattern in unique_patterns:
    if 'single-detached-house' in pattern:
        project_types.add('Single Detached House (SDH)')
    elif 'townhome' in pattern:
        project_types.add('Townhome (TH)')  
    elif 'semi-detached-house' in pattern:
        project_types.add('Semi-Detached House (SEDH)')
    elif 'apitown' in pattern:
        project_types.add('Apitown (Up-country)')
    elif 'OnlineMKT' in pattern:
        project_types.add('Online Marketing Content')
    elif 'Coupons' in pattern:
        project_types.add('Coupons/Credits')

for ptype in sorted(project_types):
    print(f"  - {ptype}")

# 2. Platform patterns
print("\n2. PLATFORMS FOUND:")
platforms = set()
for pattern in unique_patterns:
    if pattern.startswith('Instagram'):
        platforms.add('Instagram')
    elif pattern.startswith('pk|'):
        platforms.add('Facebook (direct pk)')
    elif pattern.startswith('Coupons'):
        platforms.add('Coupons/Credits')
    else:
        platforms.add('Other')

for platform in sorted(platforms):
    print(f"  - {platform}")

# 3. Objective patterns
print("\n3. OBJECTIVES FOUND:")
objectives = set()
for pattern in unique_patterns:
    obj_matches = re.findall(r'_([A-Za-z-]+)_(?:VDO|CTA|facebook|IG|CollectionCanvas|Boostpost|Combine|CLO)', pattern)
    for obj in obj_matches:
        if obj in ['Awareness', 'Conversion', 'LeadAd', 'Traffic', 'Engagement', 'View', 'Landing-Pageview']:
            objectives.add(obj)

for obj in sorted(objectives):
    print(f"  - {obj}")

# 4. Campaign type patterns  
print("\n4. CAMPAIGN TYPES FOUND:")
campaign_types = set()
for pattern in unique_patterns:
    type_matches = re.findall(r'_(VDO|CTA|CollectionCanvas|Boostpost|Combine|CLO|Carousel|Single Ads -DCO)_', pattern)
    for ctype in type_matches:
        campaign_types.add(ctype)

for ctype in sorted(campaign_types):
    print(f"  - {ctype}")

# 5. Sample patterns from each category
print(f"\n=== SAMPLE PATTERNS BY CATEGORY ===")

# SDH patterns
sdh_patterns = [p for p in unique_patterns if 'single-detached-house' in p][:3]
print(f"\nSingle Detached House samples ({len([p for p in unique_patterns if 'single-detached-house' in p])} total):")
for i, pattern in enumerate(sdh_patterns, 1):
    print(f"  {i}. {pattern}")

# Townhome patterns  
th_patterns = [p for p in unique_patterns if 'townhome' in p][:3]
print(f"\nTownhome samples ({len([p for p in unique_patterns if 'townhome' in p])} total):")
for i, pattern in enumerate(th_patterns, 1):
    print(f"  {i}. {pattern}")

# Apitown patterns
api_patterns = [p for p in unique_patterns if 'apitown' in p][:3] 
print(f"\nApitown samples ({len([p for p in unique_patterns if 'apitown' in p])} total):")
for i, pattern in enumerate(api_patterns, 1):
    print(f"  {i}. {pattern}")

# Online marketing patterns
online_patterns = [p for p in unique_patterns if 'OnlineMKT' in p][:3]
print(f"\nOnline Marketing samples ({len([p for p in unique_patterns if 'OnlineMKT' in p])} total):")
for i, pattern in enumerate(online_patterns, 1):
    print(f"  {i}. {pattern}")

print(f"\n=== EDGE CASES AND VARIATIONS ===")

# Special cases
special_cases = []
for pattern in unique_patterns:
    if 'Coupons' in pattern:
        special_cases.append(f"Credit/Coupon: {pattern}")
    elif 'none_none' in pattern:
        special_cases.append(f"None fields: {pattern}")
    elif len(pattern) > 200:
        special_cases.append(f"Very long: {pattern[:100]}...")

print("Special patterns found:")
for case in special_cases[:5]:
    print(f"  - {case}")

print(f"\n=== FINAL SUMMARY ===")
print(f"✓ Analyzed 9 Facebook AP invoices")
print(f"✓ Found {len(all_clean_patterns)} total [ST] line items")
print(f"✓ Identified {len(unique_patterns)} unique patterns")
print(f"✓ Covers {len(project_types)} project types")
print(f"✓ Includes {len(platforms)} platform types") 
print(f"✓ Contains {len(objectives)} objective types")
print(f"✓ Uses {len(campaign_types)} campaign format types")