import fitz
import re
import sys
import io
import os

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_credit_note_structure(filename):
    """Analyze the structure of a Google Credit Note"""
    print(f"\n{'='*60}")
    print(f"Analyzing Credit Note Structure: {filename}")
    print('='*60)
    
    filepath = os.path.join("Invoice for testing", filename)
    
    with fitz.open(filepath) as doc:
        # Get text from all pages
        full_text = ""
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            full_text += page_text
            
            if page_num == 1:  # Focus on page 2 where line items are
                print(f"\n--- Page 2 Content ---")
                lines = page_text.split('\n')
                
                # Find where line items start
                start_found = False
                for i, line in enumerate(lines):
                    if "คำ อธิบาย" in line or "Description" in line:
                        start_found = True
                        print(f"\nFound line items section at line {i}:")
                        print("-" * 40)
                        
                    if start_found and i < len(lines) - 1:
                        # Show lines with content
                        if line.strip():
                            print(f"{i:3d}: {line}")
                        
                        # Look for amount patterns
                        if re.match(r'^-?\d+[\d,]*\.\d{2}$', line.strip()):
                            print(f"     ^ AMOUNT: {line.strip()}")
                        
                        # Look for invalid activity
                        if "กิจกรรมที่ไม่ถูกต้อง" in line:
                            print(f"     ^ INVALID ACTIVITY START")
    
    # Analyze invalid activity patterns
    print("\n" + "="*60)
    print("Invalid Activity Pattern Analysis")
    print("="*60)
    
    # Find all invalid activity entries
    invalid_pattern = r'(-?\d+[\d,]*\.\d{2})\s*\n\s*(กิจกรรมที่ไม่ถูกต้อง[^฿]+?)(?=\n\s*-?\d+[\d,]*\.\d{2}|ยอดรวม|GST|$)'
    
    matches = re.findall(invalid_pattern, full_text, re.MULTILINE | re.DOTALL)
    
    print(f"\nFound {len(matches)} invalid activity entries using regex")
    
    for i, (amount, description) in enumerate(matches[:5]):  # Show first 5
        print(f"\n{i+1}. Amount: {amount}")
        # Clean up description
        desc_clean = ' '.join(description.split())
        print(f"   Description: {desc_clean[:100]}...")
        
        # Extract details from description
        invoice_match = re.search(r'หมายเลขใบแจ้งหนี้เดิม:\s*(\d+)', desc_clean)
        month_match = re.search(r'เดือนที่ใช้บริการ:\s*([^,]+)', desc_clean)
        campaign_match = re.search(r'ชื่อแคมเปญ:\s*([^.]+)', desc_clean)
        
        if invoice_match:
            print(f"   Original Invoice: {invoice_match.group(1)}")
        if month_match:
            print(f"   Service Month: {month_match.group(1)}")
        if campaign_match:
            campaign = campaign_match.group(1).strip()
            # Try to reconstruct pk pattern
            if 'p​' in campaign and 'k​' in campaign:
                print(f"   Campaign (fragmented): {campaign}")
                # Try to reconstruct
                reconstructed = campaign.replace('p​\nk​\n', 'pk|').replace('p​k​', 'pk|')
                print(f"   Campaign (reconstructed): {reconstructed}")
            else:
                print(f"   Campaign: {campaign}")

# Test with credit notes
credit_notes = [
    "5297692790.pdf",
    "5298281913.pdf",
    "5298615229.pdf"
]

for cn in credit_notes[:1]:  # Test first one in detail
    analyze_credit_note_structure(cn)