#!/usr/bin/env python3
"""
Page 2 Line Items Analyzer for Google Invoices
Focus on extracting line items from page 2 where they are typically located
"""

import fitz  # PyMuPDF
import json
import os
from typing import Dict, List, Any, Optional
import re

def extract_page2_line_items(pdf_path: str, filename: str) -> Dict[str, Any]:
    """Extract line items specifically from page 2"""
    print(f"\n{'='*80}")
    print(f"ANALYZING PAGE 2 LINE ITEMS: {filename}")
    print(f"{'='*80}")
    
    doc = fitz.open(pdf_path)
    results = {
        'filename': filename,
        'total_pages': len(doc),
        'line_items': [],
        'amounts_found': [],
        'descriptions_found': [],
        'text_blocks': [],
        'debug_info': {}
    }
    
    if len(doc) < 2:
        print("PDF has less than 2 pages, no page 2 to analyze")
        doc.close()
        return results
    
    page = doc[1]  # Page 2 (0-indexed)
    
    # Get text as dictionary for detailed structure
    text_dict = page.get_text("dict")
    
    # Get regular text for pattern matching
    text_content = page.get_text()
    
    print(f"Page 2 Text Preview (first 500 chars):")
    print("-" * 50)
    clean_preview = text_content[:500].encode('ascii', 'ignore').decode('ascii')
    print(clean_preview)
    print("-" * 50)
    
    # Analyze blocks and extract structured data
    line_items = analyze_page2_blocks(text_dict, text_content)
    results['line_items'] = line_items
    
    # Get all amounts and descriptions for debugging
    results['amounts_found'] = extract_all_amounts(text_content)
    results['descriptions_found'] = extract_descriptions(text_dict)
    
    # Store text blocks for manual inspection
    results['text_blocks'] = extract_text_blocks_info(text_dict)
    
    print(f"\nFound {len(line_items)} line items:")
    for i, item in enumerate(line_items, 1):
        amount = item.get('amount', 'N/A')
        desc = item.get('description', 'N/A')
        desc_preview = (desc[:50] + '...') if len(desc) > 50 else desc
        try:
            desc_preview = desc_preview.encode('ascii', 'ignore').decode('ascii')
        except:
            desc_preview = '[Thai text]'
        print(f"  {i}. Amount: {amount}, Description: {desc_preview}")
    
    doc.close()
    return results

def analyze_page2_blocks(text_dict: Dict, text_content: str) -> List[Dict[str, Any]]:
    """Analyze page 2 blocks to extract line items"""
    line_items = []
    
    # Strategy 1: Look for table-like structures
    table_items = extract_from_table_structure(text_dict)
    if table_items:
        line_items.extend(table_items)
        print(f"Found {len(table_items)} items from table structure")
    
    # Strategy 2: Look for vertical patterns (amount followed by description)
    vertical_items = extract_vertical_patterns(text_dict)
    if vertical_items:
        line_items.extend(vertical_items)
        print(f"Found {len(vertical_items)} items from vertical patterns")
    
    # Strategy 3: Look for horizontal patterns (description followed by amount on same line)
    horizontal_items = extract_horizontal_patterns(text_dict)
    if horizontal_items:
        line_items.extend(horizontal_items)
        print(f"Found {len(horizontal_items)} items from horizontal patterns")
    
    # Strategy 4: Look for fragmented text patterns (text broken across spans)
    fragment_items = extract_fragmented_patterns(text_dict, text_content)
    if fragment_items:
        line_items.extend(fragment_items)
        print(f"Found {len(fragment_items)} items from fragmented patterns")
    
    # Deduplicate based on amount and description similarity
    unique_items = deduplicate_line_items(line_items)
    
    return unique_items

def extract_from_table_structure(text_dict: Dict) -> List[Dict[str, Any]]:
    """Extract line items from table-like structures"""
    items = []
    
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:  # Text block
            lines = block.get("lines", [])
            
            # Look for consistent column structures
            if len(lines) > 2:
                # Try to detect columns by analyzing X positions
                column_data = analyze_columns(lines)
                if column_data['is_table']:
                    table_items = extract_table_rows(column_data['rows'])
                    items.extend(table_items)
    
    return items

def extract_vertical_patterns(text_dict: Dict) -> List[Dict[str, Any]]:
    """Extract items where amount is above description"""
    items = []
    
    # Get all text spans with positions
    spans_with_pos = []
    
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    bbox = span.get("bbox", [])
                    
                    if text and bbox and len(bbox) >= 4:
                        spans_with_pos.append({
                            'text': text,
                            'x': bbox[0],
                            'y': bbox[1],
                            'bbox': bbox
                        })
    
    # Sort by Y position (top to bottom)
    spans_with_pos.sort(key=lambda x: x['y'])
    
    # Look for amount patterns followed by descriptions
    amount_pattern = re.compile(r'^-?\d{1,3}(?:,\d{3})*\.?\d{0,2}$')
    
    for i, span in enumerate(spans_with_pos):
        if amount_pattern.match(span['text']):
            try:
                amount = float(span['text'].replace(',', ''))
                
                # Skip very small amounts or totals
                if abs(amount) < 100 or abs(amount) > 500000:
                    continue
                
                # Look for description in nearby spans
                description = find_nearby_description(spans_with_pos, i, span)
                
                if description:
                    items.append({
                        'amount': amount,
                        'description': description,
                        'extraction_method': 'vertical_pattern'
                    })
            except ValueError:
                continue
    
    return items

def extract_horizontal_patterns(text_dict: Dict) -> List[Dict[str, Any]]:
    """Extract items where description and amount are on same line"""
    items = []
    
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:
            for line in block.get("lines", []):
                line_text = ""
                spans = line.get("spans", [])
                
                for span in spans:
                    line_text += span.get("text", "")
                
                # Look for lines containing both description and amount
                if line_text.strip():
                    item = parse_line_for_item(line_text.strip(), spans)
                    if item:
                        items.append(item)
    
    return items

def extract_fragmented_patterns(text_dict: Dict, text_content: str) -> List[Dict[str, Any]]:
    """Extract items from fragmented text (Google's specialty)"""
    items = []
    
    # Look for known Google campaign patterns
    patterns = [
        # Pattern for campaign descriptions with amounts
        r'(pk\|.*?\|.*?)\s*(-?\d{1,3}(?:,\d{3})*\.?\d{2})',
        # Pattern for Thai credit adjustments
        r'(กิจกรรมที่ไม่ถูกต้อง.*?)\s*(-?\d{1,3}(?:,\d{3})*\.?\d{2})',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text_content, re.MULTILINE | re.DOTALL)
        for match in matches:
            try:
                description = match.group(1).strip()
                amount = float(match.group(2).replace(',', ''))
                
                if abs(amount) >= 10:  # Skip very small amounts
                    items.append({
                        'amount': amount,
                        'description': description,
                        'extraction_method': 'fragmented_pattern'
                    })
            except (ValueError, IndexError):
                continue
    
    # Alternative approach: Look for amounts and try to reconstruct descriptions
    amount_pattern = re.compile(r'(-?\d{1,3}(?:,\d{3})*\.?\d{2})')
    amount_matches = list(amount_pattern.finditer(text_content))
    
    for match in amount_matches:
        try:
            amount = float(match.group(1).replace(',', ''))
            
            if abs(amount) < 100 or abs(amount) > 500000:
                continue
            
            # Look for description context around this amount
            start_pos = max(0, match.start() - 200)
            end_pos = min(len(text_content), match.end() + 200)
            context = text_content[start_pos:end_pos]
            
            description = extract_description_from_context(context, match.group(1))
            
            if description and len(description) > 10:
                items.append({
                    'amount': amount,
                    'description': description,
                    'extraction_method': 'context_reconstruction'
                })
        except ValueError:
            continue
    
    return items

def analyze_columns(lines: List[Dict]) -> Dict[str, Any]:
    """Analyze if lines form a table structure"""
    if len(lines) < 3:
        return {'is_table': False}
    
    # Get X positions of all spans
    x_positions = []
    
    for line in lines:
        line_x_positions = []
        for span in line.get("spans", []):
            bbox = span.get("bbox", [])
            if bbox and len(bbox) >= 4:
                line_x_positions.append(bbox[0])
        
        if line_x_positions:
            x_positions.append(sorted(line_x_positions))
    
    # Check for consistent column structure
    if not x_positions:
        return {'is_table': False}
    
    # Find common X positions (columns)
    all_x = []
    for positions in x_positions:
        all_x.extend(positions)
    
    # Group similar X positions
    columns = []
    tolerance = 10.0  # 10 point tolerance
    
    for x in sorted(set(all_x)):
        found_column = False
        for col in columns:
            if abs(col - x) <= tolerance:
                found_column = True
                break
        
        if not found_column:
            columns.append(x)
    
    is_table = len(columns) >= 2 and len(x_positions) >= 3
    
    return {
        'is_table': is_table,
        'columns': columns,
        'rows': lines if is_table else []
    }

def extract_table_rows(rows: List[Dict]) -> List[Dict[str, Any]]:
    """Extract line items from table rows"""
    items = []
    
    for row in rows:
        row_text = ""
        amounts = []
        
        for span in row.get("spans", []):
            text = span.get("text", "")
            row_text += text + " "
            
            # Check if this span contains an amount
            amount_match = re.match(r'^-?\d{1,3}(?:,\d{3})*\.?\d{0,2}$', text.strip())
            if amount_match:
                try:
                    amount = float(text.strip().replace(',', ''))
                    amounts.append(amount)
                except ValueError:
                    pass
        
        # If we found exactly one amount in this row, it might be a line item
        if len(amounts) == 1 and abs(amounts[0]) >= 10:
            description = row_text.replace(str(amounts[0]), "").strip()
            if description:
                items.append({
                    'amount': amounts[0],
                    'description': description,
                    'extraction_method': 'table_row'
                })
    
    return items

def find_nearby_description(spans: List[Dict], amount_index: int, amount_span: Dict) -> Optional[str]:
    """Find description near an amount"""
    descriptions = []
    
    # Look at spans around the amount (before and after)
    search_range = 10
    start_idx = max(0, amount_index - search_range)
    end_idx = min(len(spans), amount_index + search_range)
    
    for i in range(start_idx, end_idx):
        if i == amount_index:
            continue
        
        span = spans[i]
        text = span['text'].strip()
        
        # Skip if it's another amount
        if re.match(r'^-?\d{1,3}(?:,\d{3})*\.?\d{0,2}$', text):
            continue
        
        # Skip very short text
        if len(text) < 5:
            continue
        
        # Check proximity (Y position)
        y_diff = abs(span['y'] - amount_span['y'])
        if y_diff < 50:  # Within 50 points vertically
            descriptions.append(text)
    
    return ' '.join(descriptions) if descriptions else None

def parse_line_for_item(line_text: str, spans: List[Dict]) -> Optional[Dict[str, Any]]:
    """Parse a line to extract description and amount"""
    # Look for amount at end of line
    amount_match = re.search(r'(-?\d{1,3}(?:,\d{3})*\.?\d{2})\s*$', line_text)
    
    if amount_match:
        try:
            amount = float(amount_match.group(1).replace(',', ''))
            
            if abs(amount) < 10 or abs(amount) > 500000:
                return None
            
            # Get description (everything before the amount)
            description = line_text[:amount_match.start()].strip()
            
            if description and len(description) > 5:
                return {
                    'amount': amount,
                    'description': description,
                    'extraction_method': 'horizontal_pattern'
                }
        except ValueError:
            pass
    
    return None

def extract_description_from_context(context: str, amount_str: str) -> Optional[str]:
    """Extract description from context around an amount"""
    # Remove the amount from context
    context_clean = context.replace(amount_str, ' ').strip()
    
    # Look for meaningful text patterns
    lines = context_clean.split('\n')
    
    meaningful_lines = []
    for line in lines:
        line = line.strip()
        
        # Skip very short lines
        if len(line) < 10:
            continue
        
        # Skip lines that are mostly numbers or symbols
        if re.match(r'^[\d\s,.-]+$', line):
            continue
        
        meaningful_lines.append(line)
    
    if meaningful_lines:
        # Return the longest meaningful line as description
        return max(meaningful_lines, key=len)
    
    return None

def extract_all_amounts(text_content: str) -> List[Dict[str, Any]]:
    """Extract all amounts for debugging"""
    amounts = []
    
    pattern = re.compile(r'(-?\d{1,3}(?:,\d{3})*\.?\d{0,2})')
    matches = pattern.finditer(text_content)
    
    for match in matches:
        try:
            amount = float(match.group(1).replace(',', ''))
            amounts.append({
                'value': amount,
                'text': match.group(1),
                'position': match.span()
            })
        except ValueError:
            continue
    
    return amounts

def extract_descriptions(text_dict: Dict) -> List[str]:
    """Extract potential descriptions for debugging"""
    descriptions = []
    
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                
                line_text = line_text.strip()
                
                # Keep lines that might be descriptions
                if (line_text and 
                    len(line_text) > 10 and 
                    not re.match(r'^[\d\s,.-]+$', line_text)):
                    descriptions.append(line_text)
    
    return descriptions

def extract_text_blocks_info(text_dict: Dict) -> List[Dict[str, Any]]:
    """Extract text block information for debugging"""
    blocks_info = []
    
    for i, block in enumerate(text_dict.get("blocks", [])):
        if block.get("type") == 0:
            block_text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "")
            
            blocks_info.append({
                'block_num': i,
                'bbox': block.get("bbox", []),
                'text_length': len(block_text),
                'text_preview': block_text[:100].encode('ascii', 'ignore').decode('ascii')
            })
    
    return blocks_info

def deduplicate_line_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate line items"""
    unique_items = []
    seen_combinations = set()
    
    for item in items:
        # Create a key based on amount and first 50 chars of description
        amount = item.get('amount', 0)
        desc = item.get('description', '')[:50]
        key = (amount, desc)
        
        if key not in seen_combinations:
            seen_combinations.add(key)
            unique_items.append(item)
    
    return unique_items

def analyze_all_problematic_invoices():
    """Analyze all three problematic invoices"""
    base_path = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    target_files = [
        ("5297692778.pdf", "Should have 4 items but we only get 1"),
        ("5297692787.pdf", "Should have 13 items but we only get 1"), 
        ("5300624442.pdf", "Should have multiple items")
    ]
    
    all_results = {}
    
    for filename, description in target_files:
        pdf_path = os.path.join(base_path, filename)
        
        if os.path.exists(pdf_path):
            print(f"\n{description}")
            try:
                result = extract_page2_line_items(pdf_path, filename)
                all_results[filename] = result
                
                # Save individual results
                output_file = f"page2_analysis_{filename.replace('.pdf', '')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"Page 2 analysis saved to: {output_file}")
                
            except Exception as e:
                print(f"Error analyzing {filename}: {e}")
        else:
            print(f"File not found: {pdf_path}")
    
    return all_results

if __name__ == "__main__":
    print("Page 2 Line Items Analyzer for Google Invoices")
    print("=" * 60)
    
    analyze_all_problematic_invoices()