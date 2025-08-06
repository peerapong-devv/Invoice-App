import os
import sys
import json
import PyPDF2

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import both parsers
from improved_tiktok_parser import parse_tiktok_invoice as parse_improved
from final_corrected_tiktok_parser import parse_tiktok_invoice as parse_final

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None

def debug_text_extraction(text_content, filename):
    """Debug the specific structure issues"""
    print(f"\n{'='*80}")
    print(f"DEBUGGING TEXT STRUCTURE: {filename}")
    print(f"{'='*80}")
    
    # Check the consumption details section structure
    consumption_start = text_content.find('Consumption Details:')
    if consumption_start == -1:
        print("ERROR: 'Consumption Details:' not found!")
        return
    
    # Get the consumption section
    consumption_text = text_content[consumption_start:]
    lines = consumption_text.split('\n')
    
    print(f"Found 'Consumption Details:' at position {consumption_start}")
    print(f"Lines in consumption section: {len(lines)}")
    
    # Show first 20 lines after consumption details
    print("\nFirst 20 lines after 'Consumption Details:':")
    for i, line in enumerate(lines[:20]):
        line_clean = line.strip()
        # Clean for ASCII output
        line_safe = line_clean.encode('ascii', errors='replace').decode('ascii')
        print(f"{i:2d}: '{line_safe}'")
    
    # Look for key patterns
    import re
    
    print(f"\nPattern Analysis:")
    
    # Find ST patterns and their context
    st_lines = []
    for i, line in enumerate(lines):
        if re.match(r'^ST\d{10,}$', line.strip()):
            st_lines.append((i, line.strip()))
    
    print(f"ST pattern lines found: {len(st_lines)}")
    for i, (line_num, st_id) in enumerate(st_lines):
        print(f"  ST {i+1}: Line {line_num}: {st_id}")
        
        # Show next 10 lines after each ST
        print(f"    Next 10 lines after ST:")
        for j in range(1, min(11, len(lines) - line_num)):
            if line_num + j < len(lines):
                next_line = lines[line_num + j].strip()
                next_line_safe = next_line.encode('ascii', errors='replace').decode('ascii')
                print(f"      {line_num + j:2d}: '{next_line_safe}'")
        print()
    
    # Find pk| patterns and their context
    pk_lines = []
    for i, line in enumerate(lines):
        if 'pk|' in line:
            pk_lines.append((i, line.strip()))
    
    print(f"pk| pattern lines found: {len(pk_lines)}")
    for i, (line_num, pk_line) in enumerate(pk_lines):
        pk_line_safe = pk_line.encode('ascii', errors='replace').decode('ascii')
        print(f"  pk| {i+1}: Line {line_num}: {pk_line_safe[:100]}...")

def create_fixed_parser_test(text_content, filename):
    """Create a fixed parser specifically for these issue patterns"""
    print(f"\n{'='*80}")
    print(f"TESTING FIXED PARSER: {filename}")
    print(f"{'='*80}")
    
    # Extract invoice ID
    import re
    invoice_match = re.search(r"Invoice No\.\s*([\w-]+)", text_content, re.IGNORECASE)
    invoice_id = invoice_match.group(1) if invoice_match else "Unknown"
    
    # Check AP vs Non-AP
    has_st_pattern = bool(re.search(r'ST\d{10,}', text_content))
    has_pk_pattern = bool(re.search(r'pk\|', text_content))
    is_ap = has_st_pattern and has_pk_pattern
    
    print(f"Invoice ID: {invoice_id}")
    print(f"Has ST pattern: {has_st_pattern}")
    print(f"Has pk| pattern: {has_pk_pattern}")
    print(f"Classified as: {'AP' if is_ap else 'Non-AP'}")
    
    records = []
    
    if is_ap:
        # AP Invoice logic
        consumption_start = text_content.find('Consumption Details:')
        if consumption_start != -1:
            consumption_text = text_content[consumption_start:]
            lines = consumption_text.split('\n')
            
            print(f"\nProcessing AP invoice with {len(lines)} lines")
            
            # Look for pk| lines and collect campaign data
            i = 0
            line_number = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Look for pk| pattern
                if 'pk|' in line:
                    print(f"\nFound pk| pattern at line {i}: {line[:100]}...")
                    
                    # Collect multi-line campaign description
                    campaign_parts = [line]
                    j = i + 1
                    
                    # Continue collecting until we find the amount pattern
                    while j < len(lines):
                        next_line = lines[j].strip()
                        
                        # Stop collecting if we find amount pattern
                        if re.match(r'^[\d,]+\.\d{2}$', next_line):
                            print(f"  Found amount pattern at line {j}: {next_line}")
                            break
                        
                        # Add non-empty lines to campaign description
                        if next_line and not re.match(r'^\d{4}-\d{2}-', next_line):
                            campaign_parts.append(next_line)
                        
                        j += 1
                    
                    # Join campaign description
                    campaign_desc = ''.join(campaign_parts)
                    print(f"  Campaign description: {campaign_desc[:150]}...")
                    
                    # Look for the cash amount (3rd amount in the pattern)
                    amount = None
                    k = j
                    amounts_found = []
                    
                    while k < len(lines) and k < j + 5:
                        amount_line = lines[k].strip()
                        if re.match(r'^[\d,]+\.\d{2}$', amount_line):
                            amounts_found.append(amount_line)
                            k += 1
                        else:
                            break
                    
                    print(f"  Amounts found: {amounts_found}")
                    
                    # Use the 3rd amount (cash consumption) if available
                    if len(amounts_found) >= 3:
                        amount = float(amounts_found[2].replace(',', ''))
                    elif amounts_found:
                        amount = float(amounts_found[-1].replace(',', ''))
                    
                    if amount:
                        line_number += 1
                        print(f"  Created record {line_number} with amount: {amount}")
                        
                        # Extract campaign_id from [ST] pattern
                        campaign_id = None
                        if '[ST]' in campaign_desc:
                            st_split = campaign_desc.split('[ST]')
                            if len(st_split) > 1:
                                after_st = st_split[1]
                                if after_st.startswith('|'):
                                    after_st = after_st[1:]
                                campaign_id = after_st.strip()
                        
                        record = {
                            "source_filename": filename,
                            "platform": "TikTok",
                            "invoice_type": "AP",
                            "invoice_id": invoice_id,
                            "line_number": line_number,
                            "agency": "pk",
                            "campaign_id": campaign_id,
                            "total": amount,
                            "description": campaign_desc,
                        }
                        
                        records.append(record)
                    
                    i = j
                else:
                    i += 1
    
    else:
        # Non-AP Invoice logic
        print(f"Processing Non-AP invoice - not yet implemented for these patterns")
    
    print(f"\nFinal results: {len(records)} records found")
    for i, record in enumerate(records, 1):
        print(f"  Record {i}: {record['total']} - {record['description'][:100]}...")
    
    return records

def main():
    # Test files
    test_files = [
        "Invoice for testing/THTT202502215532-Prakit Holdings Public Company Limited-Invoice.pdf",
        "Invoice for testing/THTT202502215554-Prakit Holdings Public Company Limited-Invoice.pdf"
    ]
    
    for test_file in test_files:
        pdf_path = os.path.join(os.path.dirname(__file__), test_file)
        
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            continue
        
        print(f"\n{'#'*100}")
        print(f"ANALYZING FILE: {test_file}")
        print(f"{'#'*100}")
        
        # Extract text
        text_content = extract_text_from_pdf(pdf_path)
        if text_content is None:
            continue
        
        filename = os.path.basename(test_file)
        
        # Debug the text structure
        debug_text_extraction(text_content, filename)
        
        # Test with fixed parser logic
        fixed_results = create_fixed_parser_test(text_content, filename)

if __name__ == "__main__":
    main()