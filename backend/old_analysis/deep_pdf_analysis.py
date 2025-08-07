#!/usr/bin/env python3
"""
Deep PDF Analysis for Google Invoices
Comprehensive analysis using PyMuPDF to understand internal structure and identify extraction patterns
"""

import fitz  # PyMuPDF
import json
import os
from typing import Dict, List, Any, Optional
import re

def analyze_pdf_structure(pdf_path: str, filename: str) -> Dict[str, Any]:
    """Analyze PDF structure using PyMuPDF"""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {filename}")
    print(f"{'='*80}")
    
    doc = fitz.open(pdf_path)
    analysis = {
        'filename': filename,
        'pages': len(doc),
        'page_analysis': []
    }
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        print(f"\n--- PAGE {page_num + 1} ---")
        
        # Get text as dictionary for detailed structure
        text_dict = page.get_text("dict")
        
        # Get regular text for content analysis
        text_content = page.get_text()
        
        # Analyze blocks
        page_analysis = analyze_page_blocks(text_dict, text_content, page_num + 1)
        analysis['page_analysis'].append(page_analysis)
        
        # Print key findings
        print_page_analysis(page_analysis)
    
    doc.close()
    return analysis

def analyze_page_blocks(text_dict: Dict, text_content: str, page_num: int) -> Dict[str, Any]:
    """Analyze blocks in a page"""
    analysis = {
        'page_number': page_num,
        'blocks': [],
        'amounts_found': [],
        'table_structures': [],
        'text_fragments': [],
        'line_items_candidates': []
    }
    
    # Analyze blocks
    for block_num, block in enumerate(text_dict.get("blocks", [])):
        if block.get("type") == 0:  # Text block
            block_analysis = analyze_text_block(block, block_num)
            analysis['blocks'].append(block_analysis)
            
            # Look for amounts in this block
            amounts = find_amounts_in_block(block)
            analysis['amounts_found'].extend(amounts)
            
            # Look for table structures
            table_candidates = detect_table_structures(block)
            analysis['table_structures'].extend(table_candidates)
            
            # Collect text fragments
            fragments = collect_text_fragments(block)
            analysis['text_fragments'].extend(fragments)
    
    # Identify line item patterns
    analysis['line_items_candidates'] = identify_line_item_patterns(analysis)
    
    return analysis

def analyze_text_block(block: Dict, block_num: int) -> Dict[str, Any]:
    """Analyze individual text block"""
    block_text = ""
    lines = []
    
    for line in block.get("lines", []):
        line_text = ""
        spans = []
        
        for span in line.get("spans", []):
            span_text = span.get("text", "")
            line_text += span_text
            spans.append({
                'text': span_text,
                'bbox': span.get("bbox", []),
                'font': span.get("font", ""),
                'size': span.get("size", 0),
                'flags': span.get("flags", 0)
            })
        
        lines.append({
            'text': line_text.strip(),
            'bbox': line.get("bbox", []),
            'spans': spans
        })
        
        if line_text.strip():
            block_text += line_text.strip() + "\n"
    
    return {
        'block_num': block_num,
        'bbox': block.get("bbox", []),
        'text': block_text.strip(),
        'lines': lines,
        'line_count': len(lines)
    }

def find_amounts_in_block(block: Dict) -> List[Dict[str, Any]]:
    """Find monetary amounts in a block"""
    amounts = []
    
    for line in block.get("lines", []):
        line_text = ""
        for span in line.get("spans", []):
            line_text += span.get("text", "")
        
        # Look for amount patterns
        amount_patterns = [
            r'(-?\d{1,3}(?:,\d{3})*\.\d{2})',  # Standard decimal format
            r'(-?\d+\.\d{2})',                  # Simple decimal format
            r'(-?\d{1,3}(?:,\d{3})+)',         # Comma-separated integers
        ]
        
        for pattern in amount_patterns:
            matches = re.finditer(pattern, line_text)
            for match in matches:
                try:
                    amount_str = match.group(1)
                    amount_value = float(amount_str.replace(',', ''))
                    
                    amounts.append({
                        'text': amount_str,
                        'value': amount_value,
                        'bbox': line.get("bbox", []),
                        'line_text': line_text.strip(),
                        'context': line_text.strip()
                    })
                except ValueError:
                    continue
    
    return amounts

def detect_table_structures(block: Dict) -> List[Dict[str, Any]]:
    """Detect table-like structures in block"""
    table_candidates = []
    
    lines = block.get("lines", [])
    if len(lines) < 3:  # Need at least 3 lines for a table
        return table_candidates
    
    # Look for consistent column patterns
    consistent_x_positions = find_consistent_x_positions(lines)
    
    if len(consistent_x_positions) >= 2:  # At least 2 columns
        table_candidates.append({
            'block_bbox': block.get("bbox", []),
            'columns': len(consistent_x_positions),
            'column_positions': consistent_x_positions,
            'rows': len(lines),
            'confidence': calculate_table_confidence(lines, consistent_x_positions)
        })
    
    return table_candidates

def find_consistent_x_positions(lines: List[Dict]) -> List[float]:
    """Find consistent X positions across lines (potential columns)"""
    x_positions = {}
    
    for line in lines:
        for span in line.get("spans", []):
            x = span.get("bbox", [0])[0]  # Left X position
            x_rounded = round(x, 1)  # Round to nearest 0.1
            
            if x_rounded not in x_positions:
                x_positions[x_rounded] = 0
            x_positions[x_rounded] += 1
    
    # Filter positions that appear in multiple lines
    threshold = max(2, len(lines) * 0.3)  # At least 30% of lines or minimum 2
    consistent_positions = [x for x, count in x_positions.items() if count >= threshold]
    
    return sorted(consistent_positions)

def calculate_table_confidence(lines: List[Dict], x_positions: List[float]) -> float:
    """Calculate confidence that this is a table structure"""
    if not x_positions or not lines:
        return 0.0
    
    matches = 0
    total_spans = 0
    
    tolerance = 5.0  # 5 point tolerance for position matching
    
    for line in lines:
        for span in line.get("spans", []):
            total_spans += 1
            span_x = span.get("bbox", [0])[0]
            
            # Check if span aligns with any column position
            for pos in x_positions:
                if abs(span_x - pos) <= tolerance:
                    matches += 1
                    break
    
    return matches / total_spans if total_spans > 0 else 0.0

def collect_text_fragments(block: Dict) -> List[Dict[str, Any]]:
    """Collect all text fragments with position info"""
    fragments = []
    
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text = span.get("text", "").strip()
            if text:
                fragments.append({
                    'text': text,
                    'bbox': span.get("bbox", []),
                    'font': span.get("font", ""),
                    'size': span.get("size", 0),
                    'line_bbox': line.get("bbox", [])
                })
    
    return fragments

def identify_line_item_patterns(page_analysis: Dict) -> List[Dict[str, Any]]:
    """Identify potential line item patterns"""
    patterns = []
    
    amounts = page_analysis['amounts_found']
    fragments = page_analysis['text_fragments']
    
    for amount in amounts:
        # Skip very small amounts or very large amounts (likely totals)
        if abs(amount['value']) < 10 or abs(amount['value']) > 1000000:
            continue
        
        # Find nearby text fragments that could be descriptions
        amount_bbox = amount['bbox']
        if not amount_bbox or len(amount_bbox) < 4:
            continue
        
        amount_y = amount_bbox[1]  # Top Y position
        
        # Look for text fragments above or to the left of the amount
        nearby_fragments = []
        
        for fragment in fragments:
            frag_bbox = fragment['bbox']
            if not frag_bbox or len(frag_bbox) < 4:
                continue
            
            frag_y = frag_bbox[1]
            
            # Check if fragment is on same line or nearby lines
            if abs(frag_y - amount_y) < 20:  # Within 20 points vertically
                nearby_fragments.append({
                    'fragment': fragment,
                    'distance': abs(frag_y - amount_y)
                })
        
        # Sort by distance
        nearby_fragments.sort(key=lambda x: x['distance'])
        
        if nearby_fragments:
            patterns.append({
                'amount': amount,
                'nearby_text': nearby_fragments[:5],  # Top 5 closest fragments
                'pattern_type': 'amount_with_description'
            })
    
    return patterns

def print_page_analysis(analysis: Dict):
    """Print analysis results for a page"""
    print(f"Blocks found: {len(analysis['blocks'])}")
    print(f"Amounts found: {len(analysis['amounts_found'])}")
    print(f"Table structures: {len(analysis['table_structures'])}")
    print(f"Text fragments: {len(analysis['text_fragments'])}")
    print(f"Line item candidates: {len(analysis['line_items_candidates'])}")
    
    if analysis['amounts_found']:
        print("\nAMOUNTS DETECTED:")
        for i, amount in enumerate(analysis['amounts_found'][:10], 1):  # Show first 10
            try:
                context = amount['context'][:50].encode('ascii', 'ignore').decode('ascii')
                print(f"  {i}. {amount['value']:,.2f} - Context: {context}...")
            except:
                print(f"  {i}. {amount['value']:,.2f} - Context: [Thai text]...")
    
    if analysis['table_structures']:
        print("\nTABLE STRUCTURES:")
        for i, table in enumerate(analysis['table_structures'], 1):
            print(f"  {i}. {table['columns']} columns, {table['rows']} rows, confidence: {table['confidence']:.2f}")
    
    if analysis['line_items_candidates']:
        print("\nLINE ITEM CANDIDATES:")
        for i, candidate in enumerate(analysis['line_items_candidates'][:5], 1):  # Show first 5
            amount = candidate['amount']
            nearby = candidate['nearby_text']
            print(f"  {i}. Amount: {amount['value']:,.2f}")
            if nearby:
                try:
                    context = nearby[0]['fragment']['text'][:50].encode('ascii', 'ignore').decode('ascii')
                    print(f"     Context: {context}...")
                except:
                    print(f"     Context: [Thai text]...")

def analyze_specific_invoices():
    """Analyze the three specific problematic invoices"""
    base_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    target_files = [
        ("5297692778.pdf", "Should have 4 items but we only get 1"),
        ("5297692787.pdf", "Should have 13 items but we only get 1"), 
        ("5300624442.pdf", "Should have multiple items")
    ]
    
    results = {}
    
    for filename, description in target_files:
        pdf_path = os.path.join(base_path, filename)
        
        if os.path.exists(pdf_path):
            print(f"\n{description}")
            try:
                analysis = analyze_pdf_structure(pdf_path, filename)
                results[filename] = analysis
                
                # Save detailed analysis
                output_file = f"detailed_analysis_{filename.replace('.pdf', '')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2, ensure_ascii=False)
                print(f"Detailed analysis saved to: {output_file}")
                
            except Exception as e:
                print(f"Error analyzing {filename}: {e}")
        else:
            print(f"File not found: {pdf_path}")
    
    # Generate summary report
    generate_summary_report(results)
    
    return results

def generate_summary_report(results: Dict[str, Dict]):
    """Generate summary report of findings"""
    print(f"\n{'='*80}")
    print("SUMMARY REPORT")
    print(f"{'='*80}")
    
    report = {
        'total_files_analyzed': len(results),
        'common_patterns': [],
        'extraction_challenges': [],
        'recommendations': []
    }
    
    # Analyze common patterns across files
    all_amounts = []
    all_tables = []
    all_fragments = []
    
    for filename, analysis in results.items():
        print(f"\n{filename}:")
        total_amounts = 0
        total_tables = 0
        total_candidates = 0
        
        for page in analysis['page_analysis']:
            amounts = len(page['amounts_found'])
            tables = len(page['table_structures'])
            candidates = len(page['line_items_candidates'])
            
            total_amounts += amounts
            total_tables += tables
            total_candidates += candidates
            
            all_amounts.extend(page['amounts_found'])
            all_tables.extend(page['table_structures'])
        
        print(f"  - Total amounts found: {total_amounts}")
        print(f"  - Total table structures: {total_tables}")
        print(f"  - Total line item candidates: {total_candidates}")
        
        if total_candidates < total_amounts:
            report['extraction_challenges'].append(f"{filename}: {total_amounts} amounts but only {total_candidates} candidates")
    
    # Common patterns analysis
    if all_tables:
        avg_confidence = sum(t['confidence'] for t in all_tables) / len(all_tables)
        report['common_patterns'].append(f"Average table confidence: {avg_confidence:.2f}")
        
        column_counts = {}
        for table in all_tables:
            cols = table['columns']
            column_counts[cols] = column_counts.get(cols, 0) + 1
        
        most_common_cols = max(column_counts.items(), key=lambda x: x[1])
        report['common_patterns'].append(f"Most common table structure: {most_common_cols[0]} columns ({most_common_cols[1]} occurrences)")
    
    # Generate recommendations
    if report['extraction_challenges']:
        report['recommendations'].append("Focus on improving description-amount association")
        report['recommendations'].append("Implement table-aware extraction for structured data")
    
    if all_amounts:
        small_amounts = sum(1 for a in all_amounts if abs(a['value']) < 100)
        large_amounts = sum(1 for a in all_amounts if abs(a['value']) > 100000)
        
        if small_amounts > 0:
            report['recommendations'].append(f"Filter out {small_amounts} small amounts that may be noise")
        if large_amounts > 0:
            report['recommendations'].append(f"Verify {large_amounts} large amounts that may be totals")
    
    # Print recommendations
    print(f"\nRECOMMENDATIONS:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    # Save report
    with open('pdf_analysis_summary.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nSummary report saved to: pdf_analysis_summary.json")

if __name__ == "__main__":
    print("Deep PDF Analysis for Google Invoices")
    print("="*50)
    
    analyze_specific_invoices()