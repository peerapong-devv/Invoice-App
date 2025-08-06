import os
import fitz  # PyMuPDF
import re
from collections import defaultdict

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

def detect_invoice_type(text, filename):
    """More aggressive detection of invoice type"""
    text_lower = text.lower()
    
    # Check filename first
    if "_ap_" in filename.lower() or "-ap-" in filename.lower():
        return "AP (from filename)"
    elif "_nonap_" in filename.lower() or "-nonap-" in filename.lower() or "_non-ap_" in filename.lower():
        return "Non-AP (from filename)"
    
    # Check content
    if "accounts payable" in text_lower:
        return "AP"
    elif "self-billing" in text_lower or "self billing" in text_lower:
        return "Self-Billing"
    elif "proforma" in text_lower:
        return "Proforma"
    elif "credit note" in text_lower or "credit memo" in text_lower:
        return "Credit Note"
    elif "debit note" in text_lower or "debit memo" in text_lower:
        return "Debit Note"
    elif "tax invoice" in text_lower:
        return "Tax Invoice"
    elif "commercial invoice" in text_lower:
        return "Commercial Invoice"
    
    # Check for specific patterns that might indicate invoice type
    if re.search(r'invoice\s*type\s*:\s*(\w+)', text_lower):
        match = re.search(r'invoice\s*type\s*:\s*(\w+)', text_lower)
        return match.group(1).upper()
    
    return "Standard Invoice"

def main():
    invoice_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    # Analysis containers
    platform_by_series = defaultdict(lambda: defaultdict(int))
    type_by_platform = defaultdict(lambda: defaultdict(int))
    date_patterns = defaultdict(list)
    
    print("=== DETAILED INVOICE ANALYSIS ===\n")
    print("Analyzing all invoices for AP/Non-AP patterns...\n")
    
    # Process all PDFs
    all_files = [f for f in os.listdir(invoice_dir) if f.endswith('.pdf')]
    
    for i, filename in enumerate(all_files):
        pdf_path = os.path.join(invoice_dir, filename)
        text = extract_text_from_pdf(pdf_path)
        
        # Determine series
        if filename.startswith('246'):
            series = "246_series"
        elif filename.startswith('529'):
            series = "529_series"
        elif filename.startswith('530'):
            series = "530_series"
        elif filename.startswith('THTT'):
            series = "tiktok_pattern"
        else:
            series = "other"
        
        # Detect platform
        platform = "Unknown"
        if "Facebook" in text or "Meta" in text:
            platform = "Facebook/Meta"
        elif "Google" in text:
            platform = "Google"
        elif "TikTok" in text:
            platform = "TikTok"
        
        # Detect invoice type
        inv_type = detect_invoice_type(text, filename)
        
        # Update counters
        platform_by_series[series][platform] += 1
        type_by_platform[platform][inv_type] += 1
        
        # Extract dates for pattern analysis
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
        if date_match:
            date_patterns[series].append(date_match.group())
        
        # Show progress
        if (i + 1) % 20 == 0:
            print(f"Processed {i + 1}/{len(all_files)} files...")
    
    print(f"\nTotal files processed: {len(all_files)}\n")
    
    # Report findings
    print("1. PLATFORM DISTRIBUTION BY FILE SERIES:")
    for series, platforms in sorted(platform_by_series.items()):
        print(f"\n   {series.upper()}:")
        for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {platform}: {count} files")
    
    print("\n2. INVOICE TYPE DISTRIBUTION BY PLATFORM:")
    for platform, types in sorted(type_by_platform.items()):
        print(f"\n   {platform}:")
        for inv_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {inv_type}: {count} invoices")
    
    print("\n3. DATE PATTERNS OBSERVED:")
    for series, dates in date_patterns.items():
        if dates:
            print(f"\n   {series.upper()}: Found {len(dates)} dated invoices")
            # Show sample dates
            print(f"   Sample dates: {', '.join(dates[:5])}")
    
    print("\n4. KEY FINDINGS:")
    print("   - File naming convention correlates with platform:")
    print("     * 246 series = Facebook/Meta invoices")
    print("     * 529/530 series = Google invoices")
    print("     * THTT pattern = TikTok invoices")
    print("\n   - Invoice types detected:")
    total_ap = sum(types.get("AP", 0) for types in type_by_platform.values())
    total_nonap = sum(types.get("Non-AP", 0) + types.get("Non-AP (from filename)", 0) for types in type_by_platform.values())
    print(f"     * AP invoices: {total_ap}")
    print(f"     * Non-AP invoices: {total_nonap}")
    print(f"     * Unable to determine AP/Non-AP classification from content")
    print(f"     * Most invoices appear to be standard tax invoices")
    
    # Check for any anomalies
    print("\n5. ANOMALIES OR INTERESTING PATTERNS:")
    
    # Check if there's one file with different count
    total_expected = 58 + 35 + 22 + 22  # Based on earlier counts
    if len(all_files) != total_expected:
        print(f"   - File count mismatch: Expected {total_expected}, found {len(all_files)}")
    
    # Check for consistent platform mapping
    for series, platforms in platform_by_series.items():
        if len(platforms) > 1:
            print(f"   - {series} contains invoices from multiple platforms: {list(platforms.keys())}")

if __name__ == "__main__":
    main()