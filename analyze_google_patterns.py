import sys
import os
import fitz
import re
sys.path.append('backend')

def analyze_google_invoice_patterns():
    """Analyze all Google invoices to learn correct patterns"""
    
    invoice_folder = "Invoice for testing"
    
    # Get all PDF files starting with 529 (Google invoices)
    pdf_files = [f for f in os.listdir(invoice_folder) if f.startswith('529') and f.endswith('.pdf')]
    
    print(f"Analyzing {len(pdf_files)} Google invoice files...")
    print("=" * 80)
    
    patterns_learned = {
        "invoice_total_patterns": [],
        "amount_patterns": [],
        "pk_patterns": [],
        "refund_patterns": [],
        "fee_patterns": []
    }
    
    analysis_results = []
    
    for i, filename in enumerate(sorted(pdf_files)[:10], 1):  # Analyze first 10 files in detail
        filepath = os.path.join(invoice_folder, filename)
        
        try:
            print(f"\n{i}. Analyzing {filename}...")
            
            # Extract text from all pages
            with fitz.open(filepath) as doc:
                full_text = ""
                page_texts = []
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text()
                    page_texts.append(page_text)
                    full_text += page_text + f"\n--- PAGE {page_num + 1} END ---\n"
            
            lines = full_text.split('\n')
            
            # 1. Find invoice total patterns
            print("   Looking for invoice total patterns...")
            total_patterns = []
            
            # Common total patterns in Google invoices
            for line in lines:
                line_clean = line.strip()
                
                # Pattern 1: Amount with ครบกำหนด
                if 'ครบกำหนด' in line_clean:
                    amounts = re.findall(r'฿([\d,]+\.?\d*)', line_clean)
                    if amounts:
                        total_patterns.append(("ครบกำหนด", amounts[0]))
                
                # Pattern 2: Amount Due
                if 'amount due' in line_clean.lower():
                    amounts = re.findall(r'([\d,]+\.?\d*)', line_clean)
                    if amounts:
                        total_patterns.append(("Amount Due", amounts[-1]))
                
                # Pattern 3: ยอดรวมในสกุลเงิน THB
                if 'ยอดรวมในสกุลเงิน' in line_clean and 'THB' in line_clean:
                    amounts = re.findall(r'฿([\d,]+\.?\d*)', line_clean)
                    if amounts:
                        total_patterns.append(("ยอดรวมในสกุลเงิน", amounts[0]))
                
                # Pattern 4: Large standalone amounts
                if re.match(r'^฿[\d,]+\.\d{2}$', line_clean):
                    amount = re.search(r'฿([\d,]+\.\d{2})', line_clean)
                    if amount:
                        total_patterns.append(("Standalone", amount.group(1)))
            
            print(f"     Found {len(total_patterns)} total patterns: {total_patterns}")
            
            # 2. Find line item patterns
            print("   Looking for line item patterns...")
            line_items = []
            
            for line in lines:
                line_clean = line.strip()
                
                # Pattern: Description + Amount at end
                match = re.search(r'^(.+?)\s+([\d,]+\.\d{2})$', line_clean)
                if match:
                    desc = match.group(1).strip()
                    amount = float(match.group(2).replace(',', ''))
                    
                    # Skip obvious headers/totals
                    if len(desc) > 10 and not any(skip in desc.lower() for skip in ['total', 'subtotal', 'gst', 'due']):
                        line_items.append((desc[:50], amount))
            
            print(f"     Found {len(line_items)} line items")
            
            # 3. Check for pk patterns
            print("   Looking for pk patterns...")
            pk_items = []
            
            # Clean zero-width chars and reconstruct
            clean_text = full_text.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
            
            # Look for split pk patterns
            lines_clean = clean_text.split('\n')
            reconstructed_lines = []
            
            i_line = 0
            while i_line < len(lines_clean):
                line = lines_clean[i_line].strip()
                line_clean = line.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
                
                if (line_clean == 'p' and i_line + 2 < len(lines_clean)):
                    next_line = lines_clean[i_line+1].strip().replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
                    third_line = lines_clean[i_line+2].strip().replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
                    
                    if next_line == 'k' and third_line == '|':
                        # Reconstruct pk pattern
                        chars = []
                        j = i_line
                        
                        while j < len(lines_clean) and j < i_line + 100:
                            current = lines_clean[j].strip().replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
                            
                            # Stop at amount
                            if re.match(r'^\d{1,3}(?:,\d{3})*\.\d{2}$', current):
                                reconstructed_lines.append(''.join(chars))
                                reconstructed_lines.append(current)
                                j += 1
                                break
                            # Stop at long description
                            elif len(current) > 20 and ' ' in current and j > i_line + 20:
                                reconstructed_lines.append(''.join(chars))
                                reconstructed_lines.append(current)
                                j += 1
                                break
                            
                            if current and len(current) <= 5:
                                chars.append(current)
                            elif current:
                                chars.append(current)
                            
                            j += 1
                        
                        if chars:
                            pk_pattern = ''.join(chars)
                            if 'pk|' in pk_pattern:
                                pk_items.append(pk_pattern[:100])
                        
                        i_line = j
                    else:
                        reconstructed_lines.append(line)
                        i_line += 1
                else:
                    reconstructed_lines.append(line)
                    i_line += 1
            
            print(f"     Found {len(pk_items)} pk patterns")
            if pk_items:
                for pk in pk_items[:3]:
                    print(f"       {pk}...")
            
            # 4. Look for refunds (negative amounts)
            print("   Looking for refund patterns...")
            refunds = []
            
            for line in lines:
                line_clean = line.strip()
                
                # Look for negative amounts
                neg_matches = re.findall(r'([-]\d+\.?\d*)', line_clean)
                for neg_match in neg_matches:
                    try:
                        amount = float(neg_match)
                        if -10000 <= amount <= -0.01:  # Reasonable refund range
                            desc = re.sub(r'[-]\d+\.?\d*', '', line_clean).strip()
                            if desc:
                                refunds.append((desc[:50], amount))
                    except:
                        continue
            
            print(f"     Found {len(refunds)} refunds")
            
            # Store analysis results
            result = {
                "filename": filename,
                "total_patterns": total_patterns,
                "line_items_count": len(line_items),
                "pk_patterns_count": len(pk_items),
                "refunds_count": len(refunds),
                "has_pk": len(pk_items) > 0,
                "sample_line_items": line_items[:5] if line_items else [],
                "sample_refunds": refunds[:3] if refunds else []
            }
            
            analysis_results.append(result)
            
            # Update global patterns
            patterns_learned["invoice_total_patterns"].extend(total_patterns)
            patterns_learned["pk_patterns"].extend(pk_items)
            patterns_learned["refund_patterns"].extend(refunds)
            
        except Exception as e:
            print(f"     ERROR: {e}")
    
    # Analyze patterns learned
    print("\n" + "=" * 80)
    print("PATTERN ANALYSIS SUMMARY")
    print("=" * 80)
    
    # Most common total patterns
    total_types = {}
    for pattern_type, amount in patterns_learned["invoice_total_patterns"]:
        total_types[pattern_type] = total_types.get(pattern_type, 0) + 1
    
    print("Most common invoice total patterns:")
    for pattern_type, count in sorted(total_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pattern_type}: {count} occurrences")
    
    # AP vs Non-AP distribution
    ap_count = len([r for r in analysis_results if r["has_pk"]])
    non_ap_count = len([r for r in analysis_results if not r["has_pk"]])
    
    print(f"\nAP vs Non-AP distribution (first 10 files):")
    print(f"  AP (with pk|): {ap_count}")
    print(f"  Non-AP (no pk|): {non_ap_count}")
    
    # Save detailed analysis
    import json
    with open('google_invoice_pattern_analysis.json', 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_results": analysis_results,
            "patterns_learned": {
                k: v for k, v in patterns_learned.items() 
                if k != "pk_patterns"  # Skip pk_patterns as they're too long
            },
            "summary": {
                "total_files_analyzed": len(analysis_results),
                "ap_files": ap_count,
                "non_ap_files": non_ap_count,
                "total_pattern_types": total_types
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed analysis saved to: google_invoice_pattern_analysis.json")
    
    return analysis_results, patterns_learned

if __name__ == "__main__":
    analyze_google_invoice_patterns()