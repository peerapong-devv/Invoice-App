import sys
import re
import os
import shutil
import json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(r'C:\Users\peerapong\invoice-reader-app\backend')
from app import process_invoice_file

def extract_clean_st_pattern(desc):
    """Extract clean [ST] pattern from description"""
    if not desc or '[ST]' not in desc:
        return None
    
    # Find the pattern up to [ST] and campaign ID
    pattern = r'^(.*?)\[ST\]\|([A-Z0-9]+)'
    match = re.search(pattern, desc)
    if match:
        main_part = match.group(1).strip()
        campaign_id = match.group(2)
        return f"{main_part}[ST]|{campaign_id}"
    
    return desc.strip()

def parse_st_pattern(pattern):
    """Parse [ST] pattern into structured components"""
    if not pattern:
        return None
    
    # Handle coupon patterns
    if pattern.startswith('Coupons:'):
        return {
            'type': 'coupon',
            'platform': 'Coupons',
            'agency': None,
            'project_id': None,
            'description': pattern.split('[ST]')[0].strip(),
            'campaign_id': pattern.split('|')[-1] if '|' in pattern else None,
            'original': pattern
        }
    
    # Standard pattern parsing
    parts = pattern.split(' - ', 1)
    platform = parts[0] if len(parts) > 1 else 'Unknown'
    
    if len(parts) > 1:
        remainder = parts[1]
        # Extract components using regex
        match = re.match(r'([^|]+)\|([^|]*)\|(.+)\[ST\]\|(.+)', remainder)
        if match:
            agency = match.group(1)
            project_id = match.group(2) if match.group(2) else None
            description = match.group(3)
            campaign_id = match.group(4)
            
            # Extract objective, format, period from description
            obj_match = re.search(r'_([^_]+)_([^_]+)_([^_\[]+)', description)
            objective = obj_match.group(1) if obj_match else None
            format_type = obj_match.group(2) if obj_match else None
            campaign_name = obj_match.group(3) if obj_match else None
            
            # Extract period if present
            period_match = re.search(r'_([^_]*(?:25|Jun|May|Apr|Jul|\d+-\w+))_', description)
            period = period_match.group(1) if period_match else None
            
            return {
                'type': 'standard',
                'platform': platform,
                'agency': agency,
                'project_id': project_id,
                'description': description,
                'objective': objective,
                'format': format_type,
                'campaign_name': campaign_name,
                'period': period,
                'campaign_id': campaign_id,
                'original': pattern
            }
    
    # Fallback for unmatched patterns
    return {
        'type': 'other',
        'platform': platform,
        'agency': None,
        'project_id': None,
        'description': pattern,
        'objective': None,
        'format': None,
        'campaign_name': None,
        'period': None,
        'campaign_id': pattern.split('|')[-1] if '|' in pattern else None,
        'original': pattern
    }

def create_test_cases():
    """Create comprehensive test dataset from all AP invoices"""
    
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

    test_dataset = {
        'metadata': {
            'total_invoices': len(ap_filenames),
            'extraction_date': '2025-01-22',
            'description': 'Comprehensive Facebook AP Invoice [ST] Line Item Test Dataset',
            'source': 'Real AP invoices from June 2025 billing period'
        },
        'summary': {
            'total_st_items': 0,
            'by_invoice': {},
            'by_category': {},
            'unique_patterns': 0
        },
        'test_cases': [],
        'edge_cases': [],
        'pattern_categories': {
            'project_types': set(),
            'platforms': set(),
            'objectives': set(),
            'formats': set(),
            'periods': set(),
            'campaign_ids': set()
        }
    }

    all_patterns = []
    
    print("Extracting [ST] patterns from all AP invoices...")
    
    for file_name in ap_filenames:
        file_path = os.path.join(INVOICE_DIR, file_name)
        if os.path.exists(file_path):
            dest_path = os.path.join(UPLOAD_FOLDER, file_name)
            shutil.copy(file_path, dest_path)
            
            try:
                processed_data = process_invoice_file(dest_path, file_name)
                
                st_items = []
                if processed_data:
                    for record in processed_data:
                        if record.get('description') and '[ST]' in record.get('description'):
                            clean_pattern = extract_clean_st_pattern(record.get('description'))
                            if clean_pattern:
                                parsed = parse_st_pattern(clean_pattern)
                                if parsed:
                                    st_items.append(parsed)
                                    all_patterns.append(parsed)
                
                test_dataset['summary']['by_invoice'][file_name] = len(st_items)
                print(f"  {file_name}: {len(st_items)} [ST] items")
                
            except Exception as e:
                print(f"  Error processing {file_name}: {e}")
                test_dataset['summary']['by_invoice'][file_name] = 0
            
            finally:
                if os.path.exists(dest_path):
                    os.remove(dest_path)

    # Process all patterns
    test_dataset['summary']['total_st_items'] = len(all_patterns)
    
    # Categorize patterns
    for pattern in all_patterns:
        if pattern['type'] == 'coupon':
            test_dataset['pattern_categories']['project_types'].add('Coupons/Credits')
        elif 'SDH' in pattern.get('description', ''):
            test_dataset['pattern_categories']['project_types'].add('Single Detached House (SDH)')
        elif 'townhome' in pattern.get('description', ''):
            test_dataset['pattern_categories']['project_types'].add('Townhome (TH)')
        elif 'semi-detached' in pattern.get('description', ''):
            test_dataset['pattern_categories']['project_types'].add('Semi-Detached House (SEDH)')
        elif 'apitown' in pattern.get('description', '').lower():
            test_dataset['pattern_categories']['project_types'].add('Apitown (Up-country)')
        elif 'OnlineMKT' in pattern.get('description', ''):
            test_dataset['pattern_categories']['project_types'].add('Online Marketing Content')
        
        if pattern.get('platform'):
            test_dataset['pattern_categories']['platforms'].add(pattern['platform'])
        if pattern.get('objective'):
            test_dataset['pattern_categories']['objectives'].add(pattern['objective'])
        if pattern.get('format'):
            test_dataset['pattern_categories']['formats'].add(pattern['format'])
        if pattern.get('period'):
            test_dataset['pattern_categories']['periods'].add(pattern['period'])
        if pattern.get('campaign_id'):
            test_dataset['pattern_categories']['campaign_ids'].add(pattern['campaign_id'])

    # Create test cases by category
    unique_patterns = list({p['original']: p for p in all_patterns}.values())
    test_dataset['summary']['unique_patterns'] = len(unique_patterns)

    # Group by categories
    categories = {
        'sdh_patterns': [],
        'townhome_patterns': [],
        'sedh_patterns': [],
        'apitown_patterns': [],
        'online_marketing_patterns': [],
        'coupon_patterns': []
    }
    
    for pattern in unique_patterns:
        test_case = {
            'id': f"test_{len(test_dataset['test_cases']) + 1:03d}",
            'category': '',
            'description': '',
            'input': pattern['original'],
            'expected_extraction': {
                'platform': pattern.get('platform'),
                'agency': pattern.get('agency'),
                'project_id': pattern.get('project_id'),
                'objective': pattern.get('objective'),
                'format': pattern.get('format'),
                'period': pattern.get('period'),
                'campaign_id': pattern.get('campaign_id')
            },
            'test_type': 'standard'
        }
        
        if pattern['type'] == 'coupon':
            test_case['category'] = 'Coupons/Credits'
            test_case['description'] = 'Credit adjustment line item'
            categories['coupon_patterns'].append(test_case)
        elif 'SDH' in pattern.get('description', ''):
            test_case['category'] = 'Single Detached House (SDH)'  
            test_case['description'] = 'Premium standalone house advertising'
            categories['sdh_patterns'].append(test_case)
        elif 'townhome' in pattern.get('description', ''):
            test_case['category'] = 'Townhome (TH)'
            test_case['description'] = 'Connected housing unit advertising'
            categories['townhome_patterns'].append(test_case)
        elif 'semi-detached' in pattern.get('description', ''):
            test_case['category'] = 'Semi-Detached House (SEDH)'
            test_case['description'] = 'Two-unit connected house advertising'
            categories['sedh_patterns'].append(test_case)
        elif 'apitown' in pattern.get('description', '').lower():
            test_case['category'] = 'Apitown (Up-country)'
            test_case['description'] = 'Up-country development project advertising'
            categories['apitown_patterns'].append(test_case)
        elif 'OnlineMKT' in pattern.get('description', ''):
            test_case['category'] = 'Online Marketing Content'
            test_case['description'] = 'Digital marketing content promotion'
            categories['online_marketing_patterns'].append(test_case)
        else:
            test_case['category'] = 'Other'
            test_case['description'] = 'Other advertising pattern'

        test_dataset['test_cases'].append(test_case)

    # Identify edge cases
    edge_cases = []
    for pattern in unique_patterns:
        if pattern['type'] == 'coupon':
            edge_cases.append({
                'type': 'credit_adjustment',
                'pattern': pattern['original'],
                'note': 'Negative amount credit/refund entry'
            })
        elif not pattern.get('project_id') or pattern.get('project_id') == 'none':
            edge_cases.append({
                'type': 'missing_project_id',
                'pattern': pattern['original'],
                'note': 'No explicit project ID specified'
            })
        elif len(pattern['original']) > 200:
            edge_cases.append({
                'type': 'very_long_description',
                'pattern': pattern['original'][:100] + '...',
                'note': 'Unusually long description pattern'
            })
        elif not pattern.get('period') or pattern.get('period') == 'none':
            edge_cases.append({
                'type': 'missing_period',
                'pattern': pattern['original'],
                'note': 'No period specification'
            })

    test_dataset['edge_cases'] = edge_cases

    # Convert sets to lists for JSON serialization
    for key in test_dataset['pattern_categories']:
        test_dataset['pattern_categories'][key] = sorted(list(test_dataset['pattern_categories'][key]))

    # Update category counts
    test_dataset['summary']['by_category'] = {
        'Single Detached House (SDH)': len(categories['sdh_patterns']),
        'Townhome (TH)': len(categories['townhome_patterns']),
        'Semi-Detached House (SEDH)': len(categories['sedh_patterns']),
        'Apitown (Up-country)': len(categories['apitown_patterns']),
        'Online Marketing Content': len(categories['online_marketing_patterns']),
        'Coupons/Credits': len(categories['coupon_patterns'])
    }

    return test_dataset

if __name__ == "__main__":
    print("Creating comprehensive Facebook AP [ST] test dataset...")
    dataset = create_test_cases()
    
    # Save to JSON file
    output_file = r'C:\Users\peerapong\invoice-reader-app\facebook_ap_st_comprehensive_test_dataset.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Test dataset created successfully!")
    print(f"📄 Saved to: {output_file}")
    print(f"\n📊 DATASET SUMMARY:")
    print(f"   Total invoices processed: {dataset['metadata']['total_invoices']}")
    print(f"   Total [ST] line items: {dataset['summary']['total_st_items']}")
    print(f"   Unique patterns: {dataset['summary']['unique_patterns']}")
    print(f"   Test cases generated: {len(dataset['test_cases'])}")
    print(f"   Edge cases identified: {len(dataset['edge_cases'])}")
    
    print(f"\n📋 BY CATEGORY:")
    for category, count in dataset['summary']['by_category'].items():
        print(f"   {category}: {count}")
    
    print(f"\n📋 BY INVOICE:")
    for invoice, count in dataset['summary']['by_invoice'].items():
        print(f"   {invoice}: {count}")
    
    print(f"\n🎯 PATTERN COVERAGE:")
    print(f"   Project types: {len(dataset['pattern_categories']['project_types'])}")
    print(f"   Platforms: {len(dataset['pattern_categories']['platforms'])}")
    print(f"   Objectives: {len(dataset['pattern_categories']['objectives'])}")
    print(f"   Formats: {len(dataset['pattern_categories']['formats'])}")
    print(f"   Periods: {len(dataset['pattern_categories']['periods'])}")
    print(f"   Campaign IDs: {len(dataset['pattern_categories']['campaign_ids'])}")
    
    print(f"\n🚀 Ready for comprehensive test suite implementation!")