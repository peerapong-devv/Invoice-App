import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import process_invoice_file
import json

def test_enhanced_google_parser():
    """Test enhanced Google parser with financial items tracking"""
    
    test_files = [
        ("Invoice for testing/5298248238.pdf", "AP"),
        ("Invoice for testing/5300646032.pdf", "Non-AP"),
        ("Invoice for testing/5297692787.pdf", "AP")
    ]
    
    print("=== TESTING ENHANCED GOOGLE PARSER ===\n")
    
    all_results = []
    
    for filename, expected_type in test_files:
        print(f"Testing: {filename} (Expected: {expected_type})")
        print("-" * 70)
        
        if os.path.exists(filename):
            # Create temp upload folder
            if not os.path.exists('backend/uploads'):
                os.makedirs('backend/uploads')
            
            # Copy file to uploads folder
            import shutil
            upload_path = os.path.join('backend/uploads', os.path.basename(filename))
            shutil.copy(filename, upload_path)
            
            try:
                records = process_invoice_file(upload_path, os.path.basename(filename))
                
                print(f"Found {len(records)} records")
                
                # Check if we have invoice_total
                if records and records[0].get('invoice_total'):
                    invoice_total = records[0]['invoice_total']
                    calculated_total = sum(r['total'] for r in records if r['total'])
                    
                    print(f"Invoice Total: {invoice_total:,.2f} THB")
                    print(f"Calculated Total: {calculated_total:,.2f} THB")
                    print(f"Difference: {abs(invoice_total - calculated_total):.2f} THB")
                    
                    if abs(invoice_total - calculated_total) < 0.01:
                        print("✓ Totals match!")
                    else:
                        print("✗ Totals don't match")
                
                # Group by item type
                campaigns = [r for r in records if r.get('item_type') == 'Campaign']
                refunds = [r for r in records if r.get('item_type') == 'Refund']
                fees = [r for r in records if r.get('item_type') == 'Fee']
                
                print(f"\nBreakdown:")
                print(f"  Campaigns: {len(campaigns)} items ({sum(r['total'] for r in campaigns if r['total']):,.2f} THB)")
                print(f"  Refunds: {len(refunds)} items ({sum(r['total'] for r in refunds if r['total']):,.2f} THB)")
                print(f"  Fees: {len(fees)} items ({sum(r['total'] for r in fees if r['total']):,.2f} THB)")
                
                # Show sample records
                print(f"\nSample Records:")
                for i, record in enumerate(records[:3], 1):
                    print(f"  {i}. {record.get('item_type', 'Unknown')} - {record['total']:,.2f} THB")
                    
                    if record['invoice_type'] == 'AP' and record.get('project_name'):
                        print(f"     Project: {record['project_name']}")
                        print(f"     Campaign: {record.get('campaign_id', 'N/A')}")
                    elif record['invoice_type'] == 'Non-AP':
                        desc = record['description'][:50] + "..." if len(record['description']) > 50 else record['description']
                        print(f"     Description: {desc}")
                    print()
                
                # Save detailed results
                invoice_id = records[0].get('invoice_id', 'unknown')
                output_file = f"{invoice_id}_enhanced_results.json"
                
                result_data = {
                    "filename": filename,
                    "invoice_id": invoice_id,
                    "invoice_type": expected_type,
                    "invoice_total": records[0].get('invoice_total') if records else None,
                    "calculated_total": sum(r['total'] for r in records if r['total']),
                    "total_records": len(records),
                    "campaigns": len(campaigns),
                    "refunds": len(refunds),
                    "fees": len(fees),
                    "records": records
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, indent=2, ensure_ascii=False)
                
                print(f"Detailed results saved to: {output_file}")
                all_results.append(result_data)
                
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"File not found: {filename}")
        
        print("\n" + "="*70 + "\n")
    
    # Summary
    print("=== SUMMARY ===")
    for result in all_results:
        print(f"{result['filename']}:")
        print(f"  Records: {result['total_records']} ({result['campaigns']} campaigns, {result['refunds']} refunds, {result['fees']} fees)")
        if result['invoice_total']:
            diff = abs(result['invoice_total'] - result['calculated_total'])
            status = "✓" if diff < 0.01 else "✗"
            print(f"  Total: {result['invoice_total']:,.2f} vs {result['calculated_total']:,.2f} {status}")
        print()

if __name__ == "__main__":
    test_enhanced_google_parser()