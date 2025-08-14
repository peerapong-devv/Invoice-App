#!/usr/bin/env python3
"""Count Google invoice files accurately"""

import os

invoice_dir = os.path.join('..', 'Invoice for testing')
all_files = os.listdir(invoice_dir)

# Count files starting with 5
google_files = [f for f in all_files if f.startswith('5') and f.endswith('.pdf')]
google_files.sort()

print(f"Total Google invoice files: {len(google_files)}")
print("\nAll Google files:")
for i, f in enumerate(google_files, 1):
    print(f"{i:2d}. {f}")

# Check for 5300784496.pdf specifically
if '5300784496.pdf' in google_files:
    print("\n✓ File 5300784496.pdf is in the list (might be detected as TikTok)")
else:
    print("\n✗ File 5300784496.pdf is NOT in the list")