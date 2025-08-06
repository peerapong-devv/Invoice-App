import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import process_invoice_file
import json

def test_enhanced_google_invoices():
    """Test enhanced Google parser on sample invoices"""
    
    test_files = [
        "Invoice for testing/5298248238.pdf",  # Known AP
        "Invoice for testing/5300646032.pdf",  # Known Non-AP
        "Invoice for testing/5297692787.pdf",  # Another AP
    ]
    
    print("=== TESTING ENHANCED GOOGLE PARSER ===\n")
    
    results = []
    
    for filename in test_files:
        print(f"Processing: {os.path.basename(filename)}")
        print("-" * 50)
        
        # Create temp upload folder
        if not os.path.exists('backend/uploads'):
            os.makedirs('backend/uploads')
        
        # Copy file to uploads folder
        import shutil
        upload_path = os.path.join('backend/uploads', os.path.basename(filename))
        shutil.copy(filename, upload_path)
        
        try:
            records = process_invoice_file(upload_path, os.path.basename(filename))
            
            if not records:
                print("  No records found")
                continue
            
            # Get summary info
            invoice_id = records[0].get('invoice_id', 'Unknown')
            invoice_total = records[0].get('invoice_total', 0)
            calculated_total = sum(r['total'] for r in records if r['total'])
            
            # Group by item type
            campaigns = [r for r in records if r.get('item_type') == 'Campaign']
            refunds = [r for r in records if r.get('item_type') == 'Refund']
            fees = [r for r in records if r.get('item_type') == 'Fee']
            
            campaign_total = sum(r['total'] for r in campaigns if r['total'])
            refund_total = sum(r['total'] for r in refunds if r['total'])
            fee_total = sum(r['total'] for r in fees if r['total'])
            
            print(f"  Invoice ID: {invoice_id}")
            print(f"  Type: {records[0].get('invoice_type', 'Unknown')}")
            print(f"  Invoice Total: {invoice_total:,.2f} THB")
            print(f"  Calculated Total: {calculated_total:,.2f} THB")
            
            difference = abs(invoice_total - calculated_total) if invoice_total else 0
            if difference < 0.01:
                print(f"  Status: [OK] Totals match")
            else:
                print(f"  Status: [DIFF] Difference: {difference:.2f} THB")
            
            print(f"  Breakdown:")
            print(f"    Campaigns: {len(campaigns)} items = {campaign_total:,.2f} THB")
            print(f"    Refunds: {len(refunds)} items = {refund_total:,.2f} THB")
            print(f"    Fees: {len(fees)} items = {fee_total:,.2f} THB")
            
            # Show sample records for AP invoices
            if records[0].get('invoice_type') == 'AP':
                print(f"  Sample Campaign Records:")
                for i, record in enumerate([r for r in campaigns[:2]], 1):
                    project = record.get('project_name', 'N/A')[:30]
                    campaign_id = record.get('campaign_id', 'N/A')
                    amount = record.get('total', 0)
                    print(f"    {i}. {project}... | {campaign_id} | {amount:,.2f} THB")
            
            # Store result
            result = {
                'filename': os.path.basename(filename),
                'invoice_id': invoice_id,
                'invoice_type': records[0].get('invoice_type'),
                'invoice_total': invoice_total,
                'calculated_total': calculated_total,
                'difference': difference,
                'campaigns': len(campaigns),
                'refunds': len(refunds),
                'fees': len(fees),
                'campaign_total': campaign_total,
                'refund_total': refund_total,
                'fee_total': fee_total,
                'status': 'OK' if difference < 0.01 else 'DIFF'
            }
            
            results.append(result)
            
        except Exception as e:
            print(f"  ERROR: {str(e)[:60]}...")
            results.append({
                'filename': os.path.basename(filename),
                'error': str(e)
            })
        
        print()
    
    # Summary
    print("=== SUMMARY ===")
    successful = [r for r in results if 'error' not in r]
    matched = [r for r in successful if r.get('status') == 'OK']
    
    print(f"Successfully processed: {len(successful)}/{len(results)} files")
    print(f"Total validation matches: {len(matched)}/{len(successful)} files")
    
    if successful:
        total_campaigns = sum(r['campaigns'] for r in successful)
        total_refunds = sum(r['refunds'] for r in successful) 
        total_fees = sum(r['fees'] for r in successful)
        
        print(f"Total items found:")
        print(f"  Campaigns: {total_campaigns}")
        print(f"  Refunds: {total_refunds}")
        print(f"  Fees: {total_fees}")
    
    # Save results
    with open('enhanced_google_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: enhanced_google_test_results.json")

if __name__ == "__main__":
    test_enhanced_google_invoices()