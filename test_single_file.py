#!/usr/bin/env python3
import sys
sys.path.append('backend')

from final_google_parser_with_learning import parse_google_text
import fitz

filename = '5297692778.pdf'
filepath = f'Invoice for testing/{filename}'

print(f"Testing {filename} with updated parser...")

# Read PDF text
with fitz.open(filepath) as doc:
    text_content = ''.join([page.get_text() for page in doc])

# Parse with updated parser
records = parse_google_text(text_content, filename, "Google")

print(f"\nResults:")
for i, record in enumerate(records):
    print(f"Record {i+1}:")
    print(f"  Invoice Total: {record.get('invoice_total', 'N/A')}")
    print(f"  Total: {record.get('total', 'N/A')}")
    print(f"  Type: {record.get('invoice_type', 'N/A')}")
    print(f"  Description: {record.get('description', 'N/A')}")

expected = 18550.72
actual = records[0].get('invoice_total', 0) if records else 0
print(f"\nExpected: {expected}")
print(f"Actual: {actual}")
print(f"Match: {'YES' if abs(actual - expected) < 100 else 'NO'}")