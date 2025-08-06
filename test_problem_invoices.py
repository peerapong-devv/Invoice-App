#!/usr/bin/env python3
"""
Focused test on the 2 problematic invoices: 246791975.pdf and 246865374.pdf
"""
import os
import sys
sys.path.append('backend')

import fitz  # PyMuPDF

def analyze_problem_invoices():
    """Analyze the problematic invoices to identify issues"""
    
    problem_files = [
        '246791975.pdf',  # Known total: 1,417,663.24 THB
        '246865374.pdf'
    ]
    
    test_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    print("ANALYZING PROBLEMATIC INVOICES")
    print("=" * 60)
    
    for invoice_file in problem_files:
        filepath = os.path.join(test_dir, invoice_file)
        
        if not os.path.exists(filepath):
            print(f"ERROR: File not found: {invoice_file}")
            continue
        
        print(f"\nAnalyzing: {invoice_file}")
        print("-" * 40)
        
        try:
            # Extract text directly
            doc = fitz.open(filepath)
            full_text = "\n".join(page.get_text() for page in doc)
            page_count = doc.page_count
            doc.close()
            
            print(f"Pages: {page_count}")
            print(f"Text length: {len(full_text)} characters")
            print(f"[ST] markers found: {full_text.count('[ST]')}")
            
            # Analyze line structure
            lines = full_text.split('\n')
            print(f"Total lines: {len(lines)}")
            
            # Check for specific patterns
            line_numbers = []
            amounts = []
            st_lines = []
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Check if it's a line number
                if line_stripped.isdigit() and len(line_stripped) <= 3:
                    line_numbers.append(int(line_stripped))
                
                # Check for amounts (pattern like 1,234.56)
                if '.' in line_stripped and ',' in line_stripped:
                    # Try to parse as amount
                    try:
                        amount_str = line_stripped.replace(',', '')
                        if amount_str.replace('.', '').replace('-', '').isdigit():
                            amount = float(amount_str)
                            amounts.append(amount)
                    except:
                        pass
                
                # Check for [ST] lines
                if '[ST]' in line:
                    st_lines.append(i)
            
            print(f"\nStructure Analysis:")
            print(f"Line numbers found: {len(line_numbers)}")
            if line_numbers:
                print(f"  Range: {min(line_numbers)} to {max(line_numbers)}")
            print(f"Amount values found: {len(amounts)}")
            if amounts:
                print(f"  Total: {sum(amounts):,.2f}")
                print(f"  Max: {max(amounts):,.2f}")
                print(f"  Duplicates: {len(amounts) - len(set(amounts))}")
            print(f"Lines with [ST]: {len(st_lines)}")
            
            # Check for duplicate amounts
            if invoice_file == '246791975.pdf':
                print(f"\nChecking for 1,417,663.24 duplicates:")
                duplicate_amount = 1417663.24
                count = amounts.count(duplicate_amount)
                print(f"  Found {count} occurrences of {duplicate_amount:,.2f}")
                
                # Find where they appear
                if count > 0:
                    print("  Appears at line numbers:")
                    for i, line in enumerate(lines):
                        if '1,417,663.24' in line or '1417663.24' in line:
                            # Find associated line number
                            for j in range(max(0, i-5), i):
                                if lines[j].strip().isdigit() and len(lines[j].strip()) <= 3:
                                    print(f"    Line {lines[j].strip()}")
                                    break
            
            # Sample problematic sections
            print(f"\nSample [ST] lines:")
            for idx in st_lines[:5]:
                # Show context around [ST]
                start = max(0, idx-2)
                end = min(len(lines), idx+3)
                print(f"  Lines {start}-{end}:")
                for i in range(start, end):
                    print(f"    {i}: {lines[i][:80]}...")
                print()
                
        except Exception as e:
            print(f"ERROR analyzing {invoice_file}: {e}")
            import traceback
            traceback.print_exc()

def test_with_fixed_backend():
    """Test with a fixed version of the backend parser"""
    
    print("\n\nTESTING WITH FIXED PARSER")
    print("=" * 60)
    
    # Import the current backend
    from app import parse_ap_invoice_by_lines, get_base_fields
    
    test_file = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\246791975.pdf"
    
    try:
        # Extract text
        doc = fitz.open(test_file)
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()
        
        base_fields = get_base_fields(full_text)
        records = parse_ap_invoice_by_lines(full_text, "246791975.pdf", base_fields)
        
        print(f"Records extracted: {len(records)}")
        
        # Calculate total
        total = sum(r['total'] for r in records if r['total'] is not None)
        print(f"Total amount: {total:,.2f} THB")
        print(f"Expected: 1,417,663.24 THB")
        print(f"Match: {'YES' if abs(total - 1417663.24) < 0.01 else 'NO'}")
        
        # Check for duplicate amounts
        amounts = [r['total'] for r in records if r['total'] is not None]
        duplicate_amount = 1417663.24
        duplicates = [r for r in records if r['total'] == duplicate_amount]
        
        if len(duplicates) > 1:
            print(f"\nWARNING: Found {len(duplicates)} records with amount {duplicate_amount:,.2f}")
            for dup in duplicates:
                print(f"  Line {dup['line_number']}: {dup['description'][:50]}...")
        
        # Show amount distribution
        print(f"\nAmount Distribution:")
        amount_counts = {}
        for amount in amounts:
            if amount in amount_counts:
                amount_counts[amount] += 1
            else:
                amount_counts[amount] = 1
        
        # Show amounts that appear more than once
        duplicated_amounts = [(amt, cnt) for amt, cnt in amount_counts.items() if cnt > 1]
        if duplicated_amounts:
            print("Amounts appearing multiple times:")
            for amt, cnt in sorted(duplicated_amounts, key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {amt:,.2f}: {cnt} times")
                
    except Exception as e:
        print(f"ERROR testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_problem_invoices()
    test_with_fixed_backend()