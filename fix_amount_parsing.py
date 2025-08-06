#!/usr/bin/env python3

import re

def parse_concatenated_amounts(amount_string):
    """
    Parse concatenated amount strings like '164,956.950.004,956.95'
    into separate amounts [164956.95, 0.00, 4956.95]
    """
    
    # First, let's analyze the pattern
    # The amounts are: Total Consumption, Voucher (always 0.00), Cash Consumption
    # They're concatenated without spaces
    
    # Strategy: Split by finding patterns where decimal is followed by a digit that starts a new amount
    # Look for pattern: .XX[0-9] where the [0-9] starts a new number
    
    # Clean the string
    clean_string = amount_string.strip()
    
    # Method 1: If we see "0.00" in the middle, use it as separator
    if '0.00' in clean_string and not clean_string.startswith('0.00') and not clean_string.endswith('0.00'):
        # Split around 0.00
        parts = clean_string.split('0.00')
        if len(parts) == 2:
            total = parts[0]
            cash = parts[1]
            
            # Clean up the amounts
            try:
                total_amount = float(total.replace(',', ''))
                cash_amount = float(cash.replace(',', ''))
                return [total_amount, 0.00, cash_amount]
            except:
                pass
    
    # Method 2: Use regex to find all valid amounts
    # Pattern: one or more digits, possibly with commas, followed by decimal and 2 digits
    amounts = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d{2})', clean_string)
    
    if len(amounts) >= 3:
        try:
            parsed = [float(amt.replace(',', '')) for amt in amounts[:3]]
            return parsed
        except:
            pass
    
    # Method 3: Manual parsing for specific problematic patterns
    # Pattern like "301,769.840.001,769.84"
    if re.match(r'\d+,\d+\.\d+\.00\d+,\d+\.\d+', clean_string):
        # Extract the numbers
        match = re.match(r'(\d+),(\d+)\.(\d+)0\.00(\d+),(\d+)\.(\d+)', clean_string)
        if match:
            g = match.groups()
            try:
                total = float(f"{g[0]}{g[1]}.{g[2]}")
                cash = float(f"{g[3]}{g[4]}.{g[5]}")
                return [total, 0.00, cash]
            except:
                pass
    
    return None

def test_amount_parsing():
    """Test the concatenated amount parsing"""
    
    test_cases = [
        "164,956.950.004,956.95",
        "301,769.840.001,769.84",
        "1759,614.790.0059,614.79",
        "301,742.660.001,742.66",
        "301,714.530.001,714.53",
        "164,962.270.004,962.27",
        "3039,996.340.0039,996.34",
        "164,949.410.004,949.41",
        "301,750.610.001,750.61",
        "301,745.220.001,745.22",
        "301,747.130.001,747.13",
        "301,761.980.001,761.98",
        "164,955.170.004,955.17"
    ]
    
    print("Testing amount parsing:")
    print("=" * 80)
    
    total_cash = 0
    
    for test in test_cases:
        result = parse_concatenated_amounts(test)
        if result:
            print(f"{test:30} -> Total: {result[0]:>10,.2f}, Voucher: {result[1]:>6,.2f}, Cash: {result[2]:>10,.2f}")
            total_cash += result[2]
        else:
            print(f"{test:30} -> FAILED TO PARSE")
    
    print(f"\nTotal cash amount: {total_cash:,.2f}")
    print(f"Expected total: 173,380.83")
    print(f"Difference: {abs(173380.83 - total_cash):,.2f}")

if __name__ == "__main__":
    test_amount_parsing()