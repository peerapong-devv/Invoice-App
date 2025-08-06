import fitz
import re

def test_character_reconstruction():
    """Test character reconstruction for Google invoice 5298528895.pdf"""
    
    # Read the extracted text file
    with open('5298528895_full_text.txt', 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    # Clean up problematic Unicode characters
    text_content = text_content.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    
    print("=== Original fragmented text (lines 84-410) ===")
    lines = text_content.split('\n')
    fragmented_section = lines[83:411]  # Lines 84-410 (0-indexed)
    
    for i, line in enumerate(fragmented_section[:20]):  # Show first 20 lines
        clean_line = line.strip().encode('ascii', 'ignore').decode('ascii')
        print(f"Line {84+i}: '{clean_line}'")
    
    print("\n=== Reconstruction attempt ===")
    
    # Try to reconstruct the fragmented characters
    reconstructed_chars = []
    i = 84  # Start from line 84
    
    while i < len(lines) and i < 410:
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
            
        # Clean the line 
        clean_char = line.encode('ascii', 'ignore').decode('ascii')
        
        # Check if this looks like a single character or short fragment
        if len(clean_char) <= 3 and not clean_char.isdigit():
            reconstructed_chars.append(clean_char)
        else:
            # This might be the end of fragmented section
            break
            
        i += 1
    
    reconstructed_text = ''.join(reconstructed_chars)
    print(f"Reconstructed: '{reconstructed_text}'")
    
    # Try to parse this as campaign information
    print(f"\nLength: {len(reconstructed_text)}")
    
    # Look for pk pattern
    if reconstructed_text.startswith('pk'):
        print("Starts with 'pk'")
        
        # Try to split by common delimiters
        parts = reconstructed_text.split('_')
        if len(parts) >= 2:
            print(f"Split by '_': {parts[:10]}")  # Show first 10 parts
        
        # Look for project patterns
        if 'SDH' in reconstructed_text:
            print("Contains 'SDH' project identifier")
        
        # Extract potential project_id and campaign details
        if '|' in reconstructed_text:
            pipe_parts = reconstructed_text.split('|')
            print(f"Split by '|': {pipe_parts}")
    
    print("\n=== Check lines after fragmented section ===")
    # Check what comes after the fragmented section
    for i in range(190, min(200, len(lines))):
        if lines[i].strip():
            clean_line = lines[i].strip().encode('ascii', 'ignore').decode('ascii')
            print(f"Line {i+1}: '{clean_line}'")

if __name__ == "__main__":
    test_character_reconstruction()