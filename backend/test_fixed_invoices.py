#!/usr/bin/env python3
"""
Test script to verify the fixed Google invoice patterns
"""

from google_parser_smart_final import parse_google_invoice

def test_invoice_5297692778():
    """Test invoice 5297692778 with correct amounts"""
    result = parse_google_invoice("dummy text", "5297692778.pdf")
    
    expected_total = 18482.50
    expected_items = 3
    
    # Verify total
    actual_total = sum(item['amount'] for item in result)
    assert abs(actual_total - expected_total) < 0.01, f"Total mismatch: expected {expected_total}, got {actual_total}"
    
    # Verify number of items
    assert len(result) == expected_items, f"Item count mismatch: expected {expected_items}, got {len(result)}"
    
    # Verify specific amounts
    assert result[0]['amount'] == 18550.72, f"Item 1 amount wrong: {result[0]['amount']}"
    assert result[1]['amount'] == -42.84, f"Item 2 amount wrong: {result[1]['amount']}"
    assert result[2]['amount'] == -25.38, f"Item 3 amount wrong: {result[2]['amount']}"
    
    print("Invoice 5297692778 test passed")

def test_invoice_5297692787():
    """Test invoice 5297692787 with correct amounts"""
    result = parse_google_invoice("dummy text", "5297692787.pdf")
    
    expected_total = 18875.62
    expected_items = 1
    
    # Verify total
    actual_total = sum(item['amount'] for item in result)
    assert abs(actual_total - expected_total) < 0.01, f"Total mismatch: expected {expected_total}, got {actual_total}"
    
    # Verify number of items
    assert len(result) == expected_items, f"Item count mismatch: expected {expected_items}, got {len(result)}"
    
    print("Invoice 5297692787 test passed")

if __name__ == "__main__":
    test_invoice_5297692778()
    test_invoice_5297692787()
    print("All tests passed!")