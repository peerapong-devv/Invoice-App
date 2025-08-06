#!/usr/bin/env python3
"""
Test different validation approaches to find the correct one
"""

def test_validation_approaches():
    """Test different ways to calculate validation difference"""
    
    # Data from our current parser results
    test_cases = [
        {
            'filename': '5297830454.pdf',
            'expected_diff': 1774,
            'invoice_total': 13143.56,
            'campaign_charges': 11438.30,
            'refunds': [-3.2, -337.47, -523.87, -840.72],
            'total_refunds': -1705.26
        },
        {
            'filename': '5298134610.pdf', 
            'expected_diff': 1400,
            'invoice_total': 7065.35,
            'campaign_charges': 5078.31,
            'refunds': [-135.41, -379.29, -1472.34],
            'total_refunds': -1987.04
        },
        {
            'filename': '5298157309.pdf',
            'expected_diff': 1898, 
            'invoice_total': 16667.47,
            'campaign_charges': 13676.71,
            'refunds': [-220.3, -800.02, -1970.44],
            'total_refunds': -2990.76
        },
        {
            'filename': '5298361576.pdf',
            'expected_diff': 968,
            'invoice_total': 8765.10,
            'campaign_charges': 7352.76,
            'refunds': [-101.54, -270.02, -1040.78],
            'total_refunds': -1412.34
        }
    ]
    
    print("TESTING DIFFERENT VALIDATION APPROACHES")
    print("="*60)
    
    for case in test_cases:
        print(f"\n{case['filename']}:")
        print(f"  Expected validation difference: {case['expected_diff']} THB")
        print(f"  Invoice total: {case['invoice_total']:,.2f} THB")
        
        # Approach 1: Net total vs invoice total (current approach)
        net_total = case['campaign_charges'] + case['total_refunds']
        diff1 = abs(net_total - case['invoice_total'])
        print(f"  Approach 1 (Net vs Invoice): {diff1:,.2f} THB")
        
        # Approach 2: Sum of absolute values vs invoice total
        sum_absolute = case['campaign_charges'] + abs(case['total_refunds'])
        diff2 = abs(sum_absolute - case['invoice_total'])
        print(f"  Approach 2 (Sum absolute vs Invoice): {diff2:,.2f} THB")
        
        # Approach 3: Campaign charges vs invoice total
        diff3 = abs(case['campaign_charges'] - case['invoice_total'])
        print(f"  Approach 3 (Campaigns vs Invoice): {diff3:,.2f} THB")
        
        # Approach 4: Total refunds (absolute) vs some other calculation
        diff4 = abs(case['total_refunds'])
        print(f"  Approach 4 (Just refunds absolute): {diff4:,.2f} THB")
        
        # Approach 5: Try reverse calculation - what should campaign charges be?
        correct_campaigns = case['invoice_total'] - case['expected_diff']
        print(f"  If expected diff is correct, campaigns should be: {correct_campaigns:,.2f} THB")
        print(f"  Actual campaigns: {case['campaign_charges']:,.2f} THB")
        print(f"  Difference: {abs(correct_campaigns - case['campaign_charges']):,.2f} THB")
        
        # Find which approach is closest
        approaches = [
            ("Net vs Invoice", diff1),
            ("Sum absolute vs Invoice", diff2), 
            ("Campaigns vs Invoice", diff3),
            ("Just refunds absolute", diff4)
        ]
        
        closest = min(approaches, key=lambda x: abs(x[1] - case['expected_diff']))
        print(f"  Closest approach: {closest[0]} with diff {closest[1]:,.2f} THB (error: {abs(closest[1] - case['expected_diff']):,.2f})")

if __name__ == "__main__":
    test_validation_approaches()