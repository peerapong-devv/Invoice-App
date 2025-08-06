import sys
import os
import fitz
import re
sys.path.append('backend')

def deep_analyze_google_invoices():
    """Deep analysis of Google invoices to fix all issues"""
    
    invoice_folder = "Invoice for testing"
    pdf_files = [f for f in os.listdir(invoice_folder) if f.startswith('529') and f.endswith('.pdf')]
    
    print(f"Deep analyzing {len(pdf_files)} Google invoices...")
    print("=" * 100)
    
    # Focus on first 15 files for detailed analysis
    detailed_analysis = []
    
    for i, filename in enumerate(sorted(pdf_files)[:15], 1):
        filepath = os.path.join(invoice_folder, filename)
        
        try:
            print(f"\n{i:2}. DEEP ANALYSIS: {filename}")
            print("-" * 80)
            
            # Extract text from all pages separately
            with fitz.open(filepath) as doc:
                full_text = ""
                page_texts = []
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text()
                    page_texts.append(page_text)
                    full_text += page_text + f"\n=== PAGE {page_num + 1} END ===\n"
            
            # 1. DEEP ANALYSIS OF PK PATTERNS
            print("1. PK PATTERN ANALYSIS:")
            
            # Clean text first
            clean_text = full_text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
            lines = clean_text.split('\n')
            
            # Look for p, k, | sequences
            pk_sequences = []
            for line_idx in range(len(lines) - 2):
                line1 = lines[line_idx].strip()
                line2 = lines[line_idx + 1].strip() if line_idx + 1 < len(lines) else ""
                line3 = lines[line_idx + 2].strip() if line_idx + 2 < len(lines) else ""
                
                if line1 == 'p' and line2 == 'k' and line3 == '|':
                    pk_sequences.append(line_idx)
                    print(f"   Found p-k-| sequence at lines {line_idx}-{line_idx+2}")
                    
                    # Try to reconstruct what follows
                    reconstruction = []
                    for j in range(line_idx, min(len(lines), line_idx + 50)):
                        current = lines[j].strip()
                        if current:
                            reconstruction.append(current)
                        # Stop at amount or long description
                        if re.match(r'^\d{1,3}(?:,\d{3})*\.\d{2}$', current):
                            break
                        if len(current) > 30 and ' ' in current:
                            break
                    
                    reconstructed = ''.join(reconstruction)
                    if 'pk|' in reconstructed:
                        print(f"   -> Reconstructed: {reconstructed[:100]}...")
            
            # Alternative: Look for any line containing pk (case variations)
            pk_containing_lines = []
            for line_idx, line in enumerate(lines):
                if 'pk' in line.lower() and ('|' in line or 'l' in line):
                    pk_containing_lines.append((line_idx, line.strip()))
            
            print(f"   Lines containing 'pk': {len(pk_containing_lines)}")
            for line_idx, line_content in pk_containing_lines[:3]:
                print(f"   -> Line {line_idx}: {line_content[:80]}...")
            
            # Final determination
            has_pk_patterns = len(pk_sequences) > 0 or len(pk_containing_lines) > 0
            print(f"   HAS PK PATTERNS: {has_pk_patterns}")
            
            # 2. DEEP ANALYSIS OF INVOICE TOTALS
            print("\n2. INVOICE TOTAL ANALYSIS:")
            
            # Extract all amounts from the invoice
            all_amounts = []
            amount_contexts = []
            
            for line_idx, line in enumerate(lines):
                line_clean = line.strip()
                
                # Find all amounts in this line
                amounts_in_line = re.findall(r'฿?([\d,]+\.\d{2})', line_clean)
                for amount_str in amounts_in_line:
                    try:
                        amount = float(amount_str.replace(',', ''))
                        if amount > 0:
                            all_amounts.append(amount)
                            
                            # Get context (surrounding lines)
                            context_lines = []
                            for ctx_idx in range(max(0, line_idx-1), min(len(lines), line_idx+2)):
                                context_lines.append(lines[ctx_idx].strip())
                            context = ' | '.join(context_lines)
                            
                            amount_contexts.append((amount, line_clean, context))
                    except:
                        continue
            
            # Analyze amount frequencies
            from collections import Counter
            amount_counter = Counter(all_amounts)
            most_common_amounts = amount_counter.most_common(10)
            
            print(f"   Total amounts found: {len(all_amounts)}")
            print(f"   Unique amounts: {len(set(all_amounts))}")
            print("   Most frequent amounts:")
            for amount, count in most_common_amounts:
                print(f"     {amount:,.2f} appears {count} times")
            
            # Find likely invoice total
            likely_total = None
            for amount, count in most_common_amounts:
                if count >= 2 and amount > 1000:  # Reasonable invoice minimum
                    likely_total = amount
                    break
            
            if not likely_total and all_amounts:
                # Get largest reasonable amount
                reasonable = [a for a in all_amounts if 1000 < a < 100000]
                if reasonable:
                    likely_total = max(reasonable)
            
            total_str = f"{likely_total:,.2f}" if likely_total else "NOT FOUND"
            print(f"   LIKELY INVOICE TOTAL: {total_str}")
            
            # 3. DEEP ANALYSIS OF REFUNDS
            print("\n3. REFUND ANALYSIS:")
            
            # Look for negative amounts in various ranges
            negative_amounts = []
            
            for line_idx, line in enumerate(lines):
                line_clean = line.strip()
                
                # Find negative amounts
                neg_matches = re.findall(r'([-]\d+\.?\d*)', line_clean)
                for neg_match in neg_matches:
                    try:
                        amount = float(neg_match)
                        if amount < 0:
                            # Get context
                            context_lines = []
                            for ctx_idx in range(max(0, line_idx-2), min(len(lines), line_idx+3)):
                                ctx_line = lines[ctx_idx].strip()
                                if ctx_line:
                                    context_lines.append(ctx_line)
                            
                            negative_amounts.append({
                                'amount': amount,
                                'line': line_clean,
                                'context': ' | '.join(context_lines)
                            })
                    except:
                        continue
            
            # Categorize negative amounts by range
            ranges = {
                'small': [n for n in negative_amounts if -100 <= n['amount'] < 0],
                'medium': [n for n in negative_amounts if -1000 <= n['amount'] < -100],
                'large': [n for n in negative_amounts if -10000 <= n['amount'] < -1000],
                'huge': [n for n in negative_amounts if n['amount'] < -10000]
            }
            
            print(f"   Total negative amounts: {len(negative_amounts)}")
            for range_name, range_amounts in ranges.items():
                print(f"   {range_name.upper()} (-{range_name == 'small' and '100' or range_name == 'medium' and '1K' or range_name == 'large' and '10K' or '10K+'}): {len(range_amounts)}")
                
                if range_amounts:
                    for neg in range_amounts[:2]:  # Show first 2 examples
                        print(f"     {neg['amount']}: {neg['line'][:50]}...")
            
            # Look for refund keywords
            refund_keywords = [
                'ค่าดรรมใส่ไม่ถูกต้อง', 'ค่าดรรม', 'refund', 'credit', 'adjustment',
                'หมายเลขใบแจ้งหนี้เดิม', 'ค่าธรรมเนียม'
            ]
            
            keyword_negatives = []
            for neg in negative_amounts:
                for keyword in refund_keywords:
                    if keyword in neg['context']:
                        keyword_negatives.append(neg)
                        break
            
            print(f"   Negatives with refund keywords: {len(keyword_negatives)}")
            
            # 4. DEEP ANALYSIS OF LINE ITEMS
            print("\n4. LINE ITEM ANALYSIS:")
            
            # Find all potential line items (description + amount)
            line_items = []
            for line in lines:
                line_clean = line.strip()
                
                # Pattern: text followed by amount
                match = re.search(r'^(.+?)\s+([\d,]+\.\d{2})$', line_clean)
                if match:
                    desc = match.group(1).strip()
                    amount_str = match.group(2)
                    
                    try:
                        amount = float(amount_str.replace(',', ''))
                        
                        # Filter out obvious non-items
                        if (len(desc) > 5 and 
                            not any(skip in desc.lower() for skip in ['total', 'subtotal', 'gst', 'due', 'page']) and
                            amount > 0):
                            line_items.append((desc, amount))
                    except:
                        continue
            
            print(f"   Potential line items: {len(line_items)}")
            for desc, amount in line_items[:3]:
                print(f"     {amount:,.2f}: {desc[:50]}...")
            
            # Store analysis results
            analysis_result = {
                'filename': filename,
                'has_pk_patterns': has_pk_patterns,
                'pk_sequences': len(pk_sequences),
                'pk_containing_lines': len(pk_containing_lines),
                'likely_total': likely_total,
                'total_amounts_found': len(all_amounts),
                'most_frequent_amount': most_common_amounts[0] if most_common_amounts else None,
                'negative_amounts_total': len(negative_amounts),
                'negative_ranges': {k: len(v) for k, v in ranges.items()},
                'keyword_negatives': len(keyword_negatives),
                'line_items': len(line_items)
            }
            
            detailed_analysis.append(analysis_result)
            
        except Exception as e:
            print(f"   ERROR: {e}")
    
    # SUMMARY ANALYSIS
    print("\n" + "=" * 100)
    print("DEEP ANALYSIS SUMMARY")
    print("=" * 100)
    
    # AP vs Non-AP analysis
    ap_files = [r for r in detailed_analysis if r['has_pk_patterns']]
    non_ap_files = [r for r in detailed_analysis if not r['has_pk_patterns']]
    
    print(f"AP files (with pk patterns): {len(ap_files)}")
    for r in ap_files:
        print(f"  {r['filename']}: {r['pk_sequences']} sequences, {r['pk_containing_lines']} pk lines")
    
    print(f"\nNon-AP files: {len(non_ap_files)}")
    for r in non_ap_files:
        print(f"  {r['filename']}: Total={r['likely_total']}, Items={r['line_items']}")
    
    # Refund analysis summary
    print(f"\nREFUND ANALYSIS SUMMARY:")
    total_small = sum(r['negative_ranges']['small'] for r in detailed_analysis)
    total_medium = sum(r['negative_ranges']['medium'] for r in detailed_analysis)  
    total_large = sum(r['negative_ranges']['large'] for r in detailed_analysis)
    total_huge = sum(r['negative_ranges']['huge'] for r in detailed_analysis)
    
    print(f"  Small refunds (-100 to 0): {total_small}")
    print(f"  Medium refunds (-1K to -100): {total_medium}")
    print(f"  Large refunds (-10K to -1K): {total_large}")
    print(f"  Huge refunds (< -10K): {total_huge}")
    
    # Save detailed analysis
    import json
    with open('deep_google_analysis.json', 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_files': len(detailed_analysis),
                'ap_files': len(ap_files),
                'non_ap_files': len(non_ap_files),
                'refund_ranges': {
                    'small': total_small,
                    'medium': total_medium,
                    'large': total_large,
                    'huge': total_huge
                }
            },
            'detailed_results': detailed_analysis
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed analysis saved to: deep_google_analysis.json")
    
    return detailed_analysis

if __name__ == "__main__":
    deep_analyze_google_invoices()