import fitz
import os
import re

def test_reconstruction():
    filename = '5297692778.pdf'
    filepath = os.path.join('Invoice for testing', filename)
    
    with fitz.open(filepath) as doc:
        text_content = '\n'.join([page.get_text() for page in doc])
    
    # Clean up problematic Unicode characters
    text_content = text_content.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    
    lines = text_content.split('\n')
    print("=== Testing reconstruction logic ===")
    
    # Find where pk pattern starts
    pk_start = None
    for i, line in enumerate(lines):
        if line.strip() == 'p' and i + 1 < len(lines) and lines[i+1].strip() == 'k':
            pk_start = i
            print(f"Found pk pattern starting at line {i+1}")
            break
    
    if pk_start is not None:
        # Simulate reconstruction
        chars = []
        j = pk_start
        
        print(f"Collecting characters from line {pk_start+1}:")
        while j < len(lines) and j < pk_start + 100:  # Limit for debug
            current_line = lines[j].strip()
            
            if not current_line:
                j += 1
                continue
            
            chars.append(current_line)
            print(f"Line {j+1}: '{current_line}' -> Total so far: '{''.join(chars)}'")
            
            # Check if we should stop
            if current_line.isdigit() and len(current_line) >= 3:
                print(f"Stopping at line {j+1}: Found long number '{current_line}'")
                break
            
            if len(chars) > 120:  # Stop for debug
                print(f"Stopping at line {j+1}: Reached character limit")
                break
            
            j += 1
        
        reconstructed = ''.join(chars)
        print(f"\nFinal reconstructed text: '{reconstructed}'")
        print(f"Length: {len(reconstructed)}")
        print(f"Starts with 'pk': {reconstructed.startswith('pk')}")
        
        # Test pattern matching
        pattern = r'^pk\|(\d+)\|([A-Z]{2,10})_(.+)$'
        match = re.search(pattern, reconstructed)
        if match:
            print("SUCCESS: Pattern matched!")
            print(f"  Campaign number: {match.group(1)}")
            print(f"  Project ID: {match.group(2)}")
            print(f"  Details: {match.group(3)[:50]}...")
        else:
            print("FAILED: Pattern did not match")
            print("  Testing simpler patterns...")
            
            # Test if it contains pk at all
            if 'pk' in reconstructed:
                print("  Contains 'pk': Yes")
                
                # Test if it has the | structure
                if '|' in reconstructed:
                    parts = reconstructed.split('|')
                    print(f"  Parts split by '|': {parts}")
                else:
                    print("  Contains '|': No")
            else:
                print("  Contains 'pk': No")

if __name__ == "__main__":
    test_reconstruction()