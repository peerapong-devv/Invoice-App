import fitz

def analyze_specific_invoice(pdf_path):
    """Extract and analyze specific invoice"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        filename = pdf_path.split('\\')[-1]
        print(f"=== INVOICE ANALYSIS: {filename} ===\n")
        
        # Extract key lines
        lines = text.split('\n')
        
        # Look for key indicators
        print("KEY CONTENT FOUND:")
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['invoice', 'bill', 'date', 'amount', 'total', 'ap', 'facebook', 'meta', 'google', 'tiktok', 'type']):
                print(f"  {line.strip()}")
        
        # Check specific patterns
        print("\nPLATFORM DETECTION:")
        if "Facebook" in text or "Meta" in text:
            print("  - Platform: Facebook/Meta")
        elif "Google" in text:
            print("  - Platform: Google")
        elif "TikTok" in text:
            print("  - Platform: TikTok")
        else:
            print("  - Platform: Unknown")
        
        print("\nINVOICE TYPE DETECTION:")
        text_lower = text.lower()
        if "accounts payable" in text_lower:
            print("  - Type: Accounts Payable (AP)")
        elif "self-billing" in text_lower:
            print("  - Type: Self-Billing")
        elif "tax invoice" in text_lower:
            print("  - Type: Tax Invoice")
        else:
            print("  - Type: Standard Invoice")
            
        return text
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# Check the anomaly file
print("Checking the anomaly file (247036228.pdf):")
analyze_specific_invoice(r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\247036228.pdf")

print("\n" + "="*60 + "\n")

# Check a sample from each platform to understand AP/Non-AP better
print("Checking sample Facebook/Meta invoice (246530629.pdf):")
analyze_specific_invoice(r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\246530629.pdf")

print("\n" + "="*60 + "\n")

print("Checking sample Google invoice (5297692778.pdf):")
analyze_specific_invoice(r"C:\Users\peerapong\invoice-reader-app\Invoice for testing\5297692778.pdf")