#!/usr/bin/env python3
"""
Comprehensive Facebook invoice testing - both AP and Non-AP
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import glob
sys.path.append('backend')

from app import process_invoice_file

def comprehensive_facebook_test():
    """Test ALL Facebook invoices in the directory"""
    
    test_dir = r"C:\Users\peerapong\invoice-reader-app\Invoice for testing"
    
    # Get all Facebook invoices (246xxx and 247xxx series)
    facebook_files = glob.glob(os.path.join(test_dir, '246*.pdf')) + \
                    glob.glob(os.path.join(test_dir, '247*.pdf'))
    
    # Known AP invoices from previous analysis
    known_ap_invoices = {
        '246543739.pdf', '246546622.pdf', '246578231.pdf', '246579423.pdf',
        '246727587.pdf', '246738919.pdf', '246774670.pdf', '246791975.pdf', '246865374.pdf'
    }
    
    print("COMPREHENSIVE FACEBOOK INVOICE TESTING")
    print("=" * 80)
    print(f"Total Facebook invoices found: {len(facebook_files)}")
    
    # Statistics tracking
    total_ap_found = 0
    total_nonap_found = 0
    total_ap_items = 0
    total_nonap_items = 0
    total_ap_amount = 0
    total_nonap_amount = 0
    errors = []
    
    # Track classification accuracy
    correct_ap_classification = 0
    correct_nonap_classification = 0
    misclassified = []
    
    print(f"\nProcessing invoices...")
    
    for i, filepath in enumerate(facebook_files, 1):
        filename = os.path.basename(filepath)
        expected_type = "AP" if filename in known_ap_invoices else "Non-AP"
        
        try:
            records = process_invoice_file(filepath, filename)
            
            if not records or records[0].get('platform') == 'Error':
                errors.append(f"{filename}: Processing error")
                continue
            
            # Analyze results
            ap_records = [r for r in records if r.get('invoice_type') == 'AP']
            nonap_records = [r for r in records if r.get('invoice_type') == 'Non-AP']
            
            detected_type = "AP" if ap_records else "Non-AP"
            
            # Track classification accuracy
            if expected_type == detected_type:
                if expected_type == "AP":
                    correct_ap_classification += 1
                else:
                    correct_nonap_classification += 1
            else:
                misclassified.append(f"{filename}: Expected {expected_type}, got {detected_type}")
            
            # Update statistics
            if ap_records:
                total_ap_found += 1
                total_ap_items += len(ap_records)
                total_ap_amount += sum(r['total'] for r in ap_records if r['total'] is not None)
            
            if nonap_records:
                total_nonap_found += 1
                total_nonap_items += len(nonap_records)
                total_nonap_amount += sum(r['total'] for r in nonap_records if r['total'] is not None)
            
            # Progress indicator
            if i % 10 == 0 or i == len(facebook_files):
                print(f"  Processed {i}/{len(facebook_files)} invoices...")
                
        except Exception as e:
            errors.append(f"{filename}: {str(e)}")
    
    # Print comprehensive results
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST RESULTS")
    print(f"{'='*80}")
    
    print(f"\nCLASSIFICATION ACCURACY:")
    print(f"  Total Facebook invoices: {len(facebook_files)}")
    print(f"  Expected AP invoices: {len(known_ap_invoices)}")
    print(f"  Expected Non-AP invoices: {len(facebook_files) - len(known_ap_invoices)}")
    print(f"  Detected AP invoices: {total_ap_found}")
    print(f"  Detected Non-AP invoices: {total_nonap_found}")
    print(f"  Correct AP classifications: {correct_ap_classification}/{len(known_ap_invoices)}")
    print(f"  Correct Non-AP classifications: {correct_nonap_classification}/{len(facebook_files) - len(known_ap_invoices)}")
    
    accuracy = ((correct_ap_classification + correct_nonap_classification) / len(facebook_files)) * 100
    print(f"  Overall accuracy: {accuracy:.1f}%")
    
    print(f"\nDATA EXTRACTION RESULTS:")
    print(f"  AP Invoice Data:")
    print(f"    Total AP line items extracted: {total_ap_items}")
    print(f"    Total AP amount: {total_ap_amount:,.2f} THB")
    print(f"    Average items per AP invoice: {total_ap_items/max(1,total_ap_found):.1f}")
    
    print(f"  Non-AP Invoice Data:")
    print(f"    Total Non-AP line items extracted: {total_nonap_items}")
    print(f"    Total Non-AP amount: {total_nonap_amount:,.2f} THB")
    print(f"    Average items per Non-AP invoice: {total_nonap_items/max(1,total_nonap_found):.1f}")
    
    print(f"\nCOMBINED TOTALS:")
    print(f"  Total line items: {total_ap_items + total_nonap_items}")
    print(f"  Total amount: {total_ap_amount + total_nonap_amount:,.2f} THB")
    
    # Show any errors or misclassifications
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    if misclassified:
        print(f"\nMISCLASSIFICATIONS ({len(misclassified)}):")
        for misc in misclassified:
            print(f"  {misc}")
    
    # Success indicators
    success_indicators = []
    if accuracy >= 95:
        success_indicators.append("✓ Classification accuracy excellent (95%+)")
    elif accuracy >= 90:
        success_indicators.append("! Classification accuracy good (90%+)")
    else:
        success_indicators.append("✗ Classification accuracy needs improvement (<90%)")
    
    if len(errors) == 0:
        success_indicators.append("✓ No processing errors")
    elif len(errors) <= 2:
        success_indicators.append("! Few processing errors")
    else:
        success_indicators.append("✗ Multiple processing errors")
    
    if total_ap_items + total_nonap_items > 500:
        success_indicators.append(f"✓ Good data extraction volume ({total_ap_items + total_nonap_items} items)")
    
    print(f"\nSUMMARY:")
    for indicator in success_indicators:
        print(f"  {indicator}")
    
    return {
        'total_invoices': len(facebook_files),
        'ap_invoices': total_ap_found,
        'nonap_invoices': total_nonap_found,
        'ap_items': total_ap_items,
        'nonap_items': total_nonap_items,
        'accuracy': accuracy,
        'errors': len(errors)
    }

if __name__ == "__main__":
    results = comprehensive_facebook_test()