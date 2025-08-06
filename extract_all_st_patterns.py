import sys
import re
import os
import shutil
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'C:\Users\peerapong\invoice-reader-app\backend')
from app import process_invoice_file

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

all_st_descriptions = []
invoice_data = {}

for file_name in ap_filenames:
    file_path = os.path.join(INVOICE_DIR, file_name)
    if os.path.exists(file_path):
        dest_path = os.path.join(UPLOAD_FOLDER, file_name)
        shutil.copy(file_path, dest_path)
        
        processed_data = process_invoice_file(dest_path, file_name)
        
        invoice_st_descriptions = []
        if processed_data:
            for record in processed_data:
                if record.get('description') and '[ST]' in record.get('description'):
                    # Clean up the description to get just the core part
                    desc = record.get('description').strip()
                    # Remove extra whitespace and line breaks
                    desc = re.sub(r'\s+', ' ', desc)
                    all_st_descriptions.append(desc)
                    invoice_st_descriptions.append(desc)
        
        invoice_data[file_name] = invoice_st_descriptions
        print(f"{file_name}: {len(invoice_st_descriptions)} [ST] items")
        
        if os.path.exists(dest_path):
            os.remove(dest_path)

print(f"\n=== COMPREHENSIVE ANALYSIS ===")
print(f"Total [ST] line items found across all 9 AP invoices: {len(all_st_descriptions)}")

# Analyze patterns
platforms = set()
agencies = set()
project_ids = set()
objectives = set()
campaign_types = set()
campaign_ids = set()

# Extract unique patterns
for desc in all_st_descriptions:
    # Extract platform (before first " - ")
    if " - " in desc:
        platform = desc.split(" - ")[0].strip()
        platforms.add(platform)
    
    # Extract campaign ID (after last "|")
    if "|" in desc:
        campaign_id = desc.split("|")[-1].strip()
        campaign_ids.add(campaign_id)
    
    # Extract various patterns using regex
    # Agency pattern (after platform and before project ID)
    agency_match = re.search(r' - (\w+)\|', desc)
    if agency_match:
        agencies.add(agency_match.group(1))
    
    # Project ID pattern (numbers after |)
    project_id_match = re.search(r'\|(\d+)\|', desc)
    if project_id_match:
        project_ids.add(project_id_match.group(1))
    
    # Objective pattern (common objectives)
    objectives_found = re.findall(r'_(Awareness|Conversion|LeadAd|Traffic|Engagement|View)_', desc)
    for obj in objectives_found:
        objectives.add(obj)
    
    # Campaign type pattern (common types)
    campaign_types_found = re.findall(r'_(VDO|CTA|CollectionCanvas|Boostpost|Combine|CLO)_', desc)
    for ctype in campaign_types_found:
        campaign_types.add(ctype)

print(f"\n=== UNIQUE PATTERNS FOUND ===")
print(f"Platforms: {sorted(list(platforms))}")
print(f"Agencies: {sorted(list(agencies))}")
print(f"Project IDs: {sorted(list(project_ids), key=lambda x: int(x) if x.isdigit() else 0)}")
print(f"Objectives: {sorted(list(objectives))}")
print(f"Campaign Types: {sorted(list(campaign_types))}")
print(f"Campaign IDs count: {len(campaign_ids)}")

print(f"\n=== SAMPLE [ST] DESCRIPTIONS BY INVOICE ===")
for invoice, descs in invoice_data.items():
    if descs:
        print(f"\n{invoice} ({len(descs)} items):")
        # Show first 3 unique patterns
        unique_patterns = list(set(descs))[:3]
        for i, desc in enumerate(unique_patterns, 1):
            print(f"  {i}. {desc}")

print(f"\n=== EDGE CASES AND VARIATIONS ===")
# Look for unusual patterns
special_cases = []
for desc in all_st_descriptions:
    # Look for descriptions with special characteristics
    if 'Coupons' in desc:
        special_cases.append(("Coupon/Credit", desc))
    elif 'none' in desc.lower():
        special_cases.append(("None field", desc))
    elif len(desc.split('|')) > 4:  # More than usual number of pipe separators
        special_cases.append(("Complex structure", desc))

# Show first 5 special cases
print("Special cases found:")
for case_type, desc in special_cases[:5]:
    print(f"  {case_type}: {desc[:100]}...")

print(f"\n=== SUMMARY ===")
print(f"- Processed {len(ap_filenames)} AP invoices")
print(f"- Found {len(all_st_descriptions)} total [ST] line items")
print(f"- Identified {len(platforms)} unique platforms")
print(f"- Identified {len(agencies)} unique agencies") 
print(f"- Identified {len(project_ids)} unique project IDs")
print(f"- Identified {len(objectives)} unique objectives")
print(f"- Identified {len(campaign_types)} unique campaign types")
print(f"- Identified {len(campaign_ids)} unique campaign IDs")