#!/usr/bin/env python3
"""
Comprehensive final test to fix the validation differences
"""

import os
import sys
import json
import fitz
import re
from collections import Counter

# Add backend directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def analyze_amounts_comprehensively(filename):
    """Comprehensive amount analysis"""
    file_path = os.path.join("Invoice for testing", filename)
    
    if not os.path.exists(file_path):
        return None
    
    try:
        # Extract text
        with fitz.open(file_path) as doc:
            full_text = "\n".join(page.get_text() for page in doc)
        
        lines = full_text.split('\n')
        
        # Find ALL amounts (positive and negative)
        all_amounts = []
        positive_amounts = []
        negative_amounts = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Positive amounts
            if re.match(r'^\d+[\d,]*\.\d{2}$', line):
                try:
                    amount = float(line.replace(',', ''))
                    all_amounts.append(amount)
                    positive_amounts.append(amount)
                except:
                    pass
            
            # Negative amounts
            elif re.match(r'^-\d+[\d,]*\.\d{2}$', line):
                try:
                    amount = float(line.replace(',', ''))
                    all_amounts.append(amount)
                    negative_amounts.append(amount)
                except:
                    pass
        
        # Count frequencies
        positive_counter = Counter(positive_amounts)
        negative_counter = Counter(negative_amounts)
        
        print(f"\n{filename}:")
        print(f"  Positive amounts: {len(positive_amounts)}")
        print(f"  Negative amounts: {len(negative_amounts)}")
        
        print(f"  Top positive amounts by frequency:")
        for amount, count in positive_counter.most_common(5):
            print(f"    {amount:,.2f} THB appears {count} times")
        
        print(f"  Negative amounts:")
        for amount, count in negative_counter.most_common():
            print(f"    {amount:,.2f} THB appears {count} times")
        
        # Determine the correct invoice total (most frequent positive amount with count >= 3)
        frequent_positives = [(amount, count) for amount, count in positive_counter.most_common() if count >= 3]
        
        if frequent_positives:
            invoice_total = max(frequent_positives, key=lambda x: x[0])[0]
            print(f"  Suggested invoice total: {invoice_total:,.2f} THB (appears {positive_counter[invoice_total]} times)")
        else:
            # Fallback to most frequent with count >= 2
            frequent_positives = [(amount, count) for amount, count in positive_counter.most_common() if count >= 2]
            if frequent_positives:
                invoice_total = max(frequent_positives, key=lambda x: x[0])[0]
                print(f"  Fallback invoice total: {invoice_total:,.2f} THB (appears {positive_counter[invoice_total]} times)")
            else:
                invoice_total = None
                print(f"  No clear invoice total found")
        
        # Calculate validation difference
        total_refunds = sum(negative_amounts)
        if invoice_total and total_refunds:
            net_total = invoice_total + total_refunds  # refunds are negative
            validation_difference = abs(sum(positive_amounts) - invoice_total)
            
            print(f"  Total refunds: {total_refunds:,.2f} THB")
            print(f"  Sum of all positive amounts: {sum(positive_amounts):,.2f} THB")
            print(f"  Net (invoice - refunds): {net_total:,.2f} THB")
            print(f"  Validation difference: {validation_difference:,.2f} THB")
            
            return {
                'filename': filename,
                'invoice_total': invoice_total,
                'total_refunds': total_refunds,
                'net_total': net_total,
                'validation_difference': validation_difference,
                'sum_positive': sum(positive_amounts)
            }
        
        return None
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return None

def create_corrected_parser_logic(analysis_results):
    """Create the correct parser logic based on analysis"""
    
    print(f"\n{'='*60}")
    print("CORRECTED PARSER LOGIC")
    print(f"{'='*60}")
    
    for filename, expected_diff in [
        ("5297830454.pdf", 1774),
        ("5298134610.pdf", 1400), 
        ("5298157309.pdf", 1898),
        ("5298361576.pdf", 968)
    ]:
        analysis = analysis_results.get(filename)
        if analysis:
            print(f"\n{filename}:")
            print(f"  Expected validation diff: {expected_diff} THB")
            print(f"  Actual validation diff: {analysis['validation_difference']:,.2f} THB")
            print(f"  Difference from expected: {abs(analysis['validation_difference'] - expected_diff):,.2f} THB")
            
            if abs(analysis['validation_difference'] - expected_diff) < 100:
                print(f"  Status: CORRECT!")
            else:
                print(f"  Status: NEEDS ADJUSTMENT")
                
                # Try alternative calculations
                alt_diff = abs(analysis['sum_positive'] - analysis['invoice_total'])
                print(f"  Alternative validation diff: {alt_diff:,.2f} THB")
                
                if abs(alt_diff - expected_diff) < 100:
                    print(f"  Alternative Status: CORRECT!")

def main():
    """Comprehensive analysis and fix"""
    
    problem_files = [
        ("5297830454.pdf", 1774),
        ("5298134610.pdf", 1400),
        ("5298157309.pdf", 1898),  
        ("5298361576.pdf", 968)
    ]
    
    analysis_results = {}
    
    print("COMPREHENSIVE AMOUNT ANALYSIS")
    print("="*60)
    
    for filename, expected_diff in problem_files:
        analysis = analyze_amounts_comprehensively(filename)
        if analysis:
            analysis_results[filename] = analysis
    
    # Create corrected parser logic
    create_corrected_parser_logic(analysis_results)
    
    # Save results
    with open('comprehensive_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nComprehensive analysis saved to: comprehensive_analysis_results.json")

if __name__ == "__main__":
    main()