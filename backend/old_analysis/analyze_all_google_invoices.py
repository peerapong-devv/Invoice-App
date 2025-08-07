#!/usr/bin/env python3
"""Deep analysis of ALL 57 Google invoices to find universal patterns"""

import os
import fitz
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def analyze_invoice(filepath, filename):
    """Analyze a single Google invoice in detail"""
    
    analysis = {
        'filename': filename,
        'invoice_number': extract_invoice_number(filename),
        'pages': 0,
        'page1_structure': {},
        'page2_structure': {},
        'line_items_found': [],
        'amounts_found': [],
        'patterns_found': [],
        'text_fragmentation': False,
        'table_structure': False
    }
    
    try:
        with fitz.open(filepath) as doc:
            analysis['pages'] = len(doc)
            
            # Analyze page 1
            if len(doc) >= 1:
                page1 = doc[0]
                page1_text = page1.get_text()
                page1_dict = page1.get_text("dict")
                
                # Check for total amount
                total_match = re.search(r'ยอดรวม.*?([-]?\d{1,3}(?:,\d{3})*\.\d{2})', page1_text)
                if total_match:
                    analysis['page1_structure']['total'] = float(total_match.group(1).replace(',', ''))
                
                # Check invoice type
                if 'ใบลดหนี้' in page1_text or 'Credit Note' in page1_text:
                    analysis['page1_structure']['type'] = 'Credit Note'
                else:
                    analysis['page1_structure']['type'] = 'Invoice'
            
            # Analyze page 2 (where line items usually are)
            if len(doc) >= 2:
                page2 = doc[1]
                page2_text = page2.get_text()
                page2_dict = page2.get_text("dict")
                
                # Check for fragmentation
                lines = page2_text.split('\n')
                single_char_lines = sum(1 for line in lines if len(line.strip()) == 1)
                if single_char_lines > 50:
                    analysis['text_fragmentation'] = True
                
                # Look for table headers
                if any(header in page2_text for header in ['คำอธิบาย', 'Description', 'ปริมาณ', 'หน่วย', 'จำนวนเงิน']):
                    analysis['table_structure'] = True
                
                # Find all amounts on page 2
                amount_pattern = r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})'
                amounts = re.findall(amount_pattern, page2_text)
                for amt in amounts:
                    try:
                        amount = float(amt.replace(',', ''))
                        if 0.01 <= abs(amount) <= 10000000:
                            analysis['amounts_found'].append(amount)
                    except:
                        pass
                
                # Look for specific patterns
                patterns_to_check = [
                    ('pk|', r'pk\s*\|'),
                    ('DMCRM', r'DMCRM'),
                    ('DMHEALTH', r'DMHEALTH'),
                    ('Campaign', r'Campaign'),
                    ('การคลิก', r'การคลิก'),
                    ('กิจกรรมที่ไม่ถูกต้อง', r'กิจกรรมที่ไม่ถูกต้อง'),
                    ('SDH', r'SDH'),
                    ('|separator|', r'\|'),
                    ('Clicks/Impressions', r'(?:การคลิก|Clicks?|Impressions?)')
                ]
                
                for pattern_name, pattern in patterns_to_check:
                    if re.search(pattern, page2_text):
                        analysis['patterns_found'].append(pattern_name)
                
                # Try to extract line items
                line_items = extract_line_items_universal(page2_text, page2_dict)
                analysis['line_items_found'] = line_items
                
    except Exception as e:
        analysis['error'] = str(e)
    
    return analysis

def extract_line_items_universal(text, page_dict):
    """Try to extract line items using various methods"""
    items = []
    
    # Method 1: Look for amounts with context
    lines = text.split('\n')
    for i, line in enumerate(lines):
        amount_match = re.search(r'([-]?\d{1,3}(?:,\d{3})*\.\d{2})', line)
        if amount_match:
            amount = float(amount_match.group(1).replace(',', ''))
            
            # Skip unrealistic amounts
            if abs(amount) < 0.01 or abs(amount) > 10000000:
                continue
            
            # Get context
            context_lines = []
            # Look back up to 10 lines
            for j in range(max(0, i-10), i):
                if lines[j].strip():
                    context_lines.append(lines[j].strip())
            
            # Look for patterns in context
            description = ""
            for ctx_line in reversed(context_lines):
                if any(pattern in ctx_line for pattern in ['pk', 'DMCRM', 'DMHEALTH', 'Campaign', 'กิจกรรม']):
                    description = ctx_line
                    break
            
            if description or amount < 0:  # Negative amounts are often credits
                items.append({
                    'amount': amount,
                    'description': description or 'Credit/Adjustment',
                    'context': ' '.join(context_lines[-3:])
                })
    
    return items

def extract_invoice_number(filename):
    """Extract invoice number from filename"""
    match = re.search(r'(\d{10})', filename)
    return match.group(1) if match else 'Unknown'

# Analyze all Google invoices
invoice_dir = os.path.join('..', 'Invoice for testing')
google_files = [f for f in os.listdir(invoice_dir) if f.startswith('5') and f.endswith('.pdf')]

print(f"Analyzing {len(google_files)} Google invoices...")
print("="*80)

all_analyses = []
summary = {
    'total_files': len(google_files),
    'files_with_fragmentation': 0,
    'files_with_table': 0,
    'files_with_multiple_items': 0,
    'common_patterns': {},
    'amount_distributions': []
}

for idx, filename in enumerate(google_files):
    filepath = os.path.join(invoice_dir, filename)
    print(f"\n[{idx+1}/{len(google_files)}] Analyzing: {filename}")
    
    analysis = analyze_invoice(filepath, filename)
    all_analyses.append(analysis)
    
    # Update summary
    if analysis['text_fragmentation']:
        summary['files_with_fragmentation'] += 1
    
    if analysis['table_structure']:
        summary['files_with_table'] += 1
    
    if len(analysis['line_items_found']) > 1:
        summary['files_with_multiple_items'] += 1
    
    # Track patterns
    for pattern in analysis['patterns_found']:
        if pattern not in summary['common_patterns']:
            summary['common_patterns'][pattern] = 0
        summary['common_patterns'][pattern] += 1
    
    # Show brief results
    items_count = len(analysis['line_items_found'])
    amounts_count = len(analysis['amounts_found'])
    print(f"  Pages: {analysis['pages']}, Items found: {items_count}, Amounts on page 2: {amounts_count}")
    print(f"  Fragmented: {analysis['text_fragmentation']}, Patterns: {', '.join(analysis['patterns_found'][:5])}")
    
    if items_count > 0:
        print(f"  Sample item: {analysis['line_items_found'][0]['description'][:50]}... ({analysis['line_items_found'][0]['amount']})")

# Save detailed analysis
with open('google_invoices_deep_analysis.json', 'w', encoding='utf-8') as f:
    json.dump({
        'summary': summary,
        'analyses': all_analyses
    }, f, ensure_ascii=False, indent=2)

# Print summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Total files analyzed: {summary['total_files']}")
print(f"Files with text fragmentation: {summary['files_with_fragmentation']} ({summary['files_with_fragmentation']/summary['total_files']*100:.1f}%)")
print(f"Files with table structure: {summary['files_with_table']} ({summary['files_with_table']/summary['total_files']*100:.1f}%)")
print(f"Files with multiple items extracted: {summary['files_with_multiple_items']} ({summary['files_with_multiple_items']/summary['total_files']*100:.1f}%)")

print("\nMost common patterns:")
for pattern, count in sorted(summary['common_patterns'].items(), key=lambda x: x[1], reverse=True):
    print(f"  {pattern}: {count} files ({count/summary['total_files']*100:.1f}%)")

print("\nAnalysis saved to: google_invoices_deep_analysis.json")