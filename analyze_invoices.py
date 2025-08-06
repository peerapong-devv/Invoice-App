import os
import fitz  # PyMuPDF
import re
from collections import defaultdict
import json

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def analyze_invoice(text):
    """Analyze invoice text to extract key information"""
    info = {
        "platform": "Unknown",
        "invoice_type": "Unknown",
        "currency": "Unknown",
        "amount": "Unknown",
        "date": "Unknown",
        "invoice_number": "Unknown",
        "has_vat": False,
        "company_name": "Unknown"
    }
    
    # Check for platform indicators
    if "Facebook" in text or "Meta" in text or "Meta Platforms" in text:
        info["platform"] = "Facebook/Meta"
    elif "Google" in text or "Google Asia Pacific" in text:
        info["platform"] = "Google"
    elif "TikTok" in text or "TikTok Pte" in text:
        info["platform"] = "TikTok"
    elif "X Corp" in text or "Twitter" in text:
        info["platform"] = "X/Twitter"
    
    # More comprehensive AP/Non-AP detection
    text_lower = text.lower()
    if "ap invoice" in text_lower or "ap_invoice" in text_lower or "a/p invoice" in text_lower:
        info["invoice_type"] = "AP"
    elif "non-ap" in text_lower or "non ap" in text_lower or "nonap" in text_lower:
        info["invoice_type"] = "Non-AP"
    elif "self-billing" in text_lower or "self billing" in text_lower:
        info["invoice_type"] = "Self-Billing"
    elif "tax invoice" in text_lower and "ap" not in text_lower:
        info["invoice_type"] = "Standard Tax Invoice"
    
    # Extract currency
    currency_patterns = [r'THB', r'USD', r'EUR', r'GBP', r'SGD']
    for pattern in currency_patterns:
        if re.search(pattern, text):
            info["currency"] = pattern
            break
    
    # Extract date patterns (multiple formats)
    date_patterns = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}',
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}'
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            info["date"] = date_match.group()
            break
    
    # Extract invoice number (multiple patterns)
    invoice_patterns = [
        r'Invoice\s*(?:Number|No\.?|#)?\s*:?\s*(\S+)',
        r'Invoice\s*ID\s*:?\s*(\S+)',
        r'Document\s*(?:Number|No\.?)\s*:?\s*(\S+)',
        r'Bill\s*(?:Number|No\.?)\s*:?\s*(\S+)'
    ]
    for pattern in invoice_patterns:
        invoice_match = re.search(pattern, text, re.IGNORECASE)
        if invoice_match:
            info["invoice_number"] = invoice_match.group(1)
            break
    
    # Check for VAT
    if "VAT" in text or "V.A.T" in text or "Value Added Tax" in text:
        info["has_vat"] = True
    
    # Extract company name (for bill-to)
    company_patterns = [
        r'Bill\s*to\s*:?\s*([^\n]+)',
        r'Sold\s*to\s*:?\s*([^\n]+)',
        r'Customer\s*:?\s*([^\n]+)'
    ]
    for pattern in company_patterns:
        company_match = re.search(pattern, text, re.IGNORECASE)
        if company_match:
            info["company_name"] = company_match.group(1).strip()
            break
    
    return info

def main():
    invoice_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    # Categories based on filename patterns
    categories = {
        "246_series": [],
        "529_series": [],
        "530_series": [],
        "tiktok_pattern": []
    }
    
    # Platform and type counters
    platform_count = defaultdict(int)
    invoice_type_count = defaultdict(int)
    
    # Process all PDF files
    for filename in os.listdir(invoice_dir):
        if filename.endswith('.pdf'):
            # Categorize by filename
            if filename.startswith('246'):
                categories["246_series"].append(filename)
            elif filename.startswith('529'):
                categories["529_series"].append(filename)
            elif filename.startswith('530'):
                categories["530_series"].append(filename)
            elif filename.startswith('THTT'):
                categories["tiktok_pattern"].append(filename)
    
    # Analyze samples from each category
    samples_analysis = {}
    
    for category, files in categories.items():
        if files:
            # Analyze first 3 files from each category
            sample_files = files[:3]
            samples_analysis[category] = []
            
            for file in sample_files:
                pdf_path = os.path.join(invoice_dir, file)
                text = extract_text_from_pdf(pdf_path)
                info = analyze_invoice(text)
                info["filename"] = file
                samples_analysis[category].append(info)
                
                # Update counters
                platform_count[info["platform"]] += 1
                invoice_type_count[info["invoice_type"]] += 1
    
    # Print analysis results
    print("=== INVOICE ANALYSIS REPORT ===\n")
    
    print("1. FILE DISTRIBUTION BY NAMING PATTERN:")
    print(f"   - 246 series: {len(categories['246_series'])} files")
    print(f"   - 529 series: {len(categories['529_series'])} files")
    print(f"   - 530 series: {len(categories['530_series'])} files")
    print(f"   - TikTok pattern (THTT): {len(categories['tiktok_pattern'])} files")
    print(f"   - Total: {sum(len(files) for files in categories.values())} files\n")
    
    print("2. SAMPLE ANALYSIS BY CATEGORY:")
    for category, samples in samples_analysis.items():
        print(f"\n   {category.upper()}:")
        for sample in samples:
            print(f"   - {sample['filename']}")
            print(f"     Platform: {sample['platform']}")
            print(f"     Type: {sample['invoice_type']}")
            print(f"     Currency: {sample['currency']}")
            print(f"     Date: {sample['date']}")
            print(f"     Company: {sample['company_name']}")
            print(f"     Has VAT: {sample['has_vat']}")
    
    print("\n3. FILENAME PATTERNS OBSERVED:")
    print("   - 246XXXXXX.pdf: 9-digit numeric pattern")
    print("   - 529XXXXXXX.pdf: 10-digit numeric pattern starting with 529")
    print("   - 530XXXXXXX.pdf: 10-digit numeric pattern starting with 530")
    print("   - THTTYYYYMMDDXXXX-Prakit Holdings Public Company Limited-Invoice.pdf")
    print("     (TikTok invoices with date pattern: YYYYMMDD)")
    
    # Analyze all files for comprehensive platform distribution
    print("\n4. COMPREHENSIVE PLATFORM ANALYSIS:")
    all_platform_count = defaultdict(int)
    all_type_count = defaultdict(int)
    
    for filename in os.listdir(invoice_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(invoice_dir, filename)
            text = extract_text_from_pdf(pdf_path)
            info = analyze_invoice(text)
            all_platform_count[info["platform"]] += 1
            all_type_count[info["invoice_type"]] += 1
    
    print("\n   Platform Distribution:")
    for platform, count in sorted(all_platform_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {platform}: {count} invoices")
    
    print("\n   Invoice Type Distribution:")
    for inv_type, count in sorted(all_type_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {inv_type}: {count} invoices")

if __name__ == "__main__":
    main()