#!/usr/bin/env python3
"""
Analyze validation differences in the 4 problematic AP files
"""

import os
import sys
import json
import fitz  # PyMuPDF

# Add backend directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def extract_text_safely(file_path):
    """Extract text from PDF safely"""
    try:
        with fitz.open(file_path) as doc:
            full_text = "\n".join(page.get_text() for page in doc)
        return full_text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

def analyze_google_invoice(filename, text_content):
    """Analyze a Google invoice and understand the validation differences"""
    
    print(f"\n{'='*60}")
    print(f"Analyzing: {filename}")
    print(f"{'='*60}")
    
    try:
        # Check if this is detected as a credit note
        credit_keywords = ["กิจกรรมที่ไม่ถูกต้อง", "credit note", "ใบลดหนี้", "คืนเงิน", "-฿"]
        has_credit_keywords = any(keyword in text_content.lower() for keyword in credit_keywords)
        
        print(f"Credit note detected: {has_credit_keywords}")
        
        # Try enhanced credit note parser first
        if has_credit_keywords:
            try:
                from enhanced_credit_note_parser import parse_google_credit_note_enhanced, validate_credit_note_totals
                print("Trying enhanced credit note parser...")
                
                records = parse_google_credit_note_enhanced(text_content, filename)
                if records:
                    validation = validate_credit_note_totals(records)
                    print(f"Credit note parser: {len(records)} records")
                    print(f"Validation: {validation.get('message', 'No message')}")
                    
                    total_amount = sum(r.get('total', 0) for r in records if r.get('total'))
                    print(f"Total from credit note parser: {total_amount:,.2f} THB")
                    return records, total_amount, 'credit_note'
                
            except Exception as e:
                print(f"Credit note parser failed: {e}")
        
        # Try enhanced parser
        try:
            from fixed_google_parser_5298528895 import parse_google_invoice_fixed, validate_enhanced_totals
            print("Trying enhanced parser...")
            
            records = parse_google_invoice_fixed(text_content, filename)
            validation = validate_enhanced_totals(records)
            
            print(f"Enhanced parser: {len(records)} records")
            print(f"Validation: {validation.get('message', 'No message')}")
            
            if records and validation.get('invoice_total'):
                total_amount = sum(r.get('total', 0) for r in records if r.get('total'))
                print(f"Total from enhanced parser: {total_amount:,.2f} THB")
                print(f"Expected invoice total: {validation.get('invoice_total', 0):,.2f} THB")
                return records, total_amount, 'enhanced'
            
        except Exception as e:
            print(f"Enhanced parser failed: {e}")
        
        # Try perfect parser as fallback
        try:
            from perfect_google_parser import parse_google_invoice_perfect, validate_perfect_totals
            print("Trying perfect parser...")
            
            records = parse_google_invoice_perfect(text_content, filename)
            validation = validate_perfect_totals(records)
            
            print(f"Perfect parser: {len(records)} records")
            print(f"Validation: {validation.get('message', 'No message')}")
            
            total_amount = sum(r.get('total', 0) for r in records if r.get('total'))
            print(f"Total from perfect parser: {total_amount:,.2f} THB")
            return records, total_amount, 'perfect'
            
        except Exception as e:
            print(f"Perfect parser failed: {e}")
            
        print("All parsers failed!")
        return [], 0, 'failed'
        
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")
        return [], 0, 'error'

def find_amounts_in_text(text_content):
    """Find all amounts in the text to understand the expected totals"""
    import re
    
    # Look for patterns like "13,143.56" or "13143.56"
    amount_patterns = [
        r'(\d{1,3}(?:,\d{3})*\.\d{2})',  # 1,234.56 format
        r'(\d+\.\d{2})'  # 1234.56 format
    ]
    
    amounts = []
    for pattern in amount_patterns:
        matches = re.findall(pattern, text_content)
        for match in matches:
            try:
                # Convert to float
                amount = float(match.replace(',', ''))
                if amount > 10:  # Filter out very small amounts
                    amounts.append(amount)
            except:
                continue
    
    # Count frequency of amounts
    amount_counts = {}
    for amount in amounts:
        amount_counts[amount] = amount_counts.get(amount, 0) + 1
    
    # Sort by frequency then by amount
    sorted_amounts = sorted(amount_counts.items(), key=lambda x: (-x[1], -x[0]))
    
    print(f"Amount frequencies (top 10):")
    for amount, count in sorted_amounts[:10]:
        print(f"  {amount:,.2f} THB appears {count} times")
    
    return sorted_amounts

def main():
    """Analyze the 4 problematic files"""
    
    problem_files = [
        ("5297830454.pdf", 1774),  # Expected diff: 1,774 THB
        ("5298134610.pdf", 1400),  # Expected diff: 1,400 THB  
        ("5298157309.pdf", 1898),  # Expected diff: 1,898 THB
        ("5298361576.pdf", 968)    # Expected diff: 968 THB
    ]
    
    results = {}
    
    for filename, expected_diff in problem_files:
        file_path = os.path.join("Invoice for testing", filename)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        # Extract text
        text_content = extract_text_safely(file_path)
        if not text_content:
            print(f"Could not extract text from {filename}")
            continue
        
        print(f"Text length: {len(text_content)} characters")
        
        # Find amounts in text
        amount_frequencies = find_amounts_in_text(text_content)
        
        # Analyze with current parsers
        records, total_amount, parser_used = analyze_google_invoice(filename, text_content)
        
        results[filename] = {
            'expected_diff': expected_diff,
            'parsed_total': total_amount,
            'record_count': len(records),
            'parser_used': parser_used,
            'amount_frequencies': amount_frequencies[:5],  # Top 5 amounts
            'text_length': len(text_content)
        }
        
        print(f"Expected validation difference: {expected_diff} THB")
        print(f"Parsed total: {total_amount:,.2f} THB")
        
        # Try to estimate what the "correct" total should be
        if amount_frequencies:
            most_frequent_amount = amount_frequencies[0][0]
            print(f"Most frequent amount: {most_frequent_amount:,.2f} THB")
            
            # Check if our parsed total matches expected validation
            actual_diff = abs(total_amount - most_frequent_amount)
            print(f"Actual validation difference: {actual_diff:,.2f} THB")
            
            if abs(actual_diff - expected_diff) < 50:  # Within 50 THB tolerance
                print("V Validation difference matches expected!")
            else:
                print("X Validation difference does NOT match expected")
    
    # Save results
    print(f"\n{'='*60}")
    print("SUMMARY OF ALL FILES")
    print(f"{'='*60}")
    
    for filename, result in results.items():
        print(f"\n{filename}:")
        print(f"  Expected diff: {result['expected_diff']} THB")
        print(f"  Parsed total: {result['parsed_total']:,.2f} THB")
        print(f"  Records: {result['record_count']}")
        print(f"  Parser used: {result['parser_used']}")
        if result['amount_frequencies']:
            most_frequent = result['amount_frequencies'][0]
            print(f"  Most frequent amount: {most_frequent[0]:,.2f} THB ({most_frequent[1]} times)")
    
    # Save detailed results
    with open('validation_differences_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed analysis saved to: validation_differences_analysis.json")

if __name__ == "__main__":
    main()