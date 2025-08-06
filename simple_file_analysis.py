#!/usr/bin/env python3
"""
Simple analysis of problematic files without encoding issues
"""

import os
import fitz
import re
import json

def analyze_file_structure(filename):
    """Analyze file structure and return data"""
    file_path = os.path.join("Invoice for testing", filename)
    
    if not os.path.exists(file_path):
        return None
    
    try:
        # Extract text
        with fitz.open(file_path) as doc:
            full_text = "\n".join(page.get_text() for page in doc)
        
        lines = full_text.split('\n')
        
        # Check structure
        has_credit_keywords = any(keyword in full_text for keyword in ["กิจกรรมที่ไม่ถูกต้อง", "credit note", "ใบลดหนี้", "คืนเงิน"])
        has_negative_baht = "-฿" in full_text
        
        # Find all amounts
        positive_amounts = []
        negative_amounts = []
        
        for line in lines:
            line = line.strip()
            # Positive amounts
            if re.match(r'^\d+[\d,]*\.\d{2}$', line):
                try:
                    amount = float(line.replace(',', ''))
                    positive_amounts.append(amount)
                except:
                    pass
            # Negative amounts
            elif re.match(r'^-\d+[\d,]*\.\d{2}$', line):
                try:
                    amount = float(line.replace(',', ''))
                    negative_amounts.append(amount)
                except:
                    pass
        
        # Look for invoice total
        invoice_total = None
        invoice_total_patterns = [
            r'(\d{1,3}(?:,\d{3})*\.\d{2})',  # Any amount format
        ]
        
        # Count amount frequencies
        from collections import Counter
        counter = Counter(positive_amounts)
        most_common_positive = counter.most_common(3)
        
        # Check if this looks like a mixed invoice (has both positive charges and negative refunds)
        # vs pure credit note (only negative amounts)
        is_mixed_invoice = len(positive_amounts) > len(negative_amounts) and len(positive_amounts) > 5
        
        # For mixed invoices, the most frequent positive amount is likely the invoice total
        if is_mixed_invoice and most_common_positive:
            invoice_total = most_common_positive[0][0]  # Most frequent positive amount
        
        return {
            'filename': filename,
            'has_credit_keywords': has_credit_keywords,
            'has_negative_baht': has_negative_baht,
            'positive_count': len(positive_amounts),
            'negative_count': len(negative_amounts),
            'is_mixed_invoice': is_mixed_invoice,
            'most_common_positive': most_common_positive,
            'estimated_invoice_total': invoice_total,
            'text_length': len(full_text)
        }
        
    except Exception as e:
        return {'filename': filename, 'error': str(e)}

def main():
    """Analyze all problematic files"""
    
    problem_files = [
        "5297830454.pdf",  # diff: 1,774 THB
        "5298134610.pdf",  # diff: 1,400 THB
        "5298157309.pdf",  # diff: 1,898 THB  
        "5298361576.pdf"   # diff: 968 THB
    ]
    
    results = {}
    
    for filename in problem_files:
        analysis = analyze_file_structure(filename)
        if analysis:
            results[filename] = analysis
            
            print(f"\n{filename}:")
            print(f"  Credit keywords: {analysis.get('has_credit_keywords', False)}")
            print(f"  Negative baht: {analysis.get('has_negative_baht', False)}")
            print(f"  Positive amounts: {analysis.get('positive_count', 0)}")
            print(f"  Negative amounts: {analysis.get('negative_count', 0)}")
            print(f"  Mixed invoice: {analysis.get('is_mixed_invoice', False)}")
            if analysis.get('most_common_positive'):
                print(f"  Most common positive amounts: {analysis['most_common_positive']}")
            if analysis.get('estimated_invoice_total'):
                print(f"  Estimated invoice total: {analysis['estimated_invoice_total']:,.2f} THB")
    
    # Save results
    with open('file_structure_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis saved to: file_structure_analysis.json")

if __name__ == "__main__":
    main()