import fitz
import re

# Deep check on the known AP invoice
pdf_file = "Invoice for testing/5298248238.pdf"

print(f"=== Deep Analysis: {pdf_file} ===\n")

with fitz.open(pdf_file) as doc:
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"

# Save to file for analysis
with open('google_ap_full_text.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)

print(f"Total text length: {len(full_text)}")
print(f"Saved full text to: google_ap_full_text.txt")

# Look for character sequences
print("\nSearching for 'p' followed by 'k' patterns...")

# Find all 'p' characters
p_positions = [i for i, c in enumerate(full_text) if c == 'p']
print(f"Found {len(p_positions)} 'p' characters")

# Check what follows each 'p'
pk_sequences = []
for pos in p_positions[:20]:  # Check first 20
    if pos + 10 < len(full_text):
        next_chars = full_text[pos:pos+10]
        if 'k' in next_chars:
            pk_sequences.append((pos, next_chars))

print(f"\nFound {len(pk_sequences)} potential pk sequences:")
for pos, seq in pk_sequences[:5]:
    print(f"  Position {pos}: {repr(seq)}")

# Look for the specific text pattern we know exists
print("\nSearching for known patterns...")

# The pattern from our previous test
known_pattern = "20023"
if known_pattern in full_text:
    pos = full_text.find(known_pattern)
    print(f"\nFound '20023' at position {pos}")
    print(f"Context: {repr(full_text[pos-20:pos+30])}")
    
# Check line by line
print("\nChecking lines that might contain pk|...")
lines = full_text.split('\n')
relevant_lines = []

for i, line in enumerate(lines):
    # Look for lines that might be part of pk| pattern
    if any(char in line for char in ['p', 'k', '|', '2', '0']) and len(line.strip()) < 10:
        relevant_lines.append((i, line))

print(f"\nPotentially relevant short lines:")
for i, (line_no, line) in enumerate(relevant_lines[:30]):
    print(f"  Line {line_no}: {repr(line)}")

# Check for the invoice items section
print("\nLooking for invoice items section...")
for i, line in enumerate(lines):
    if "6,632.93" in line or "6632.93" in line:
        print(f"\nFound amount 6,632.93 at line {i}")
        print(f"Previous 10 lines:")
        for j in range(max(0, i-10), i):
            print(f"  {j}: {repr(lines[j])}")