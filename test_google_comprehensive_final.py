import json
import os
import sys
import fitz
from datetime import datetime

# Add backend directory to path
sys.path.append('backend')
from app import parse_google_text

def test_all_google_invoices():
    """Test all 57 Google invoices with updated parser and generate final report"""
    
    invoice_dir = r'C:\Users\peerapong\invoice-reader-app\Invoice for testing'
    
    # Get all PDF files in the directory
    all_files = [f for f in os.listdir(invoice_dir) if f.endswith('.pdf')]
    
    # Filter Google invoices (starting with 52 or 53)
    google_files = [f for f in all_files if f.startswith(('52', '53'))]
    google_files.sort()
    
    print(f"Found {len(google_files)} Google invoice files")
    
    # Comprehensive report data
    report_data = {
        "report_metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": len(google_files),
            "parser_version": "improved_google_parser_with_character_fragmentation_fix"
        },
        "summary": {
            "successful_files": 0,
            "error_files": 0,
            "total_records": 0,
            "campaign_records": 0,
            "refund_records": 0,
            "fee_records": 0,
            "total_amount_thb": 0.0
        },
        "detailed_results": [],
        "error_files": [],
        "sample_records": []
    }
    
    successful_count = 0
    error_count = 0
    
    for i, filename in enumerate(google_files, 1):
        print(f"\nProcessing {i}/{len(google_files)}: {filename}")
        
        try:
            filepath = os.path.join(invoice_dir, filename)
            
            # Extract text using PyMuPDF (same as backend)
            with fitz.open(filepath) as doc:
                text_content = '\n'.join([page.get_text() for page in doc])
            
            # Parse using the updated Google parser
            records = parse_google_text(text_content, filename, 'Google')
            
            if records:
                successful_count += 1
                
                # Calculate totals for this file
                file_amount = sum(record.get('total', 0) or 0 for record in records)
                campaign_count = len([r for r in records if r.get('item_type') == 'Campaign'])
                refund_count = len([r for r in records if r.get('item_type') == 'Refund'])  
                fee_count = len([r for r in records if r.get('item_type') == 'Fee'])
                
                # Update summary
                report_data["summary"]["total_records"] += len(records)
                report_data["summary"]["campaign_records"] += campaign_count
                report_data["summary"]["refund_records"] += refund_count
                report_data["summary"]["fee_records"] += fee_count
                report_data["summary"]["total_amount_thb"] += file_amount
                
                # Add to detailed results
                file_result = {
                    "filename": filename,
                    "status": "success",
                    "records_count": len(records),
                    "file_total_thb": round(file_amount, 2),
                    "campaign_count": campaign_count,
                    "refund_count": refund_count,
                    "fee_count": fee_count,
                    "invoice_id": records[0].get('invoice_id') if records else None,
                    "parser_used": "improved" if any("character fragmentation" in str(record.get('description', '')) for record in records) else "standard"
                }
                
                # Add sample record for first few files
                if len(report_data["sample_records"]) < 10:
                    sample_record = records[0].copy() if records else {}
                    # Clean up for JSON serialization
                    for key, value in sample_record.items():
                        if value is None:
                            sample_record[key] = ""
                    report_data["sample_records"].append({
                        "filename": filename,
                        "sample_record": sample_record
                    })
                
                report_data["detailed_results"].append(file_result)
                
                print(f"  SUCCESS: {len(records)} records, Total: {file_amount:,.2f} THB")
                
                # Show key details for first record
                if records:
                    first_record = records[0]
                    project_id = first_record.get('project_id', 'None')
                    campaign_id = first_record.get('campaign_id', 'None')
                    print(f"     Project ID: {project_id}, Campaign ID: {campaign_id}")
                
            else:
                error_count += 1
                print(f"  ERROR: No records extracted")
                
                report_data["error_files"].append({
                    "filename": filename,
                    "error": "No records extracted",
                    "status": "failed_extraction"
                })
                
        except Exception as e:
            error_count += 1
            error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            print(f"  ERROR: {error_msg}")
            
            report_data["error_files"].append({
                "filename": filename,
                "error": error_msg,
                "status": "exception"
            })
    
    # Update final summary
    report_data["summary"]["successful_files"] = successful_count
    report_data["summary"]["error_files"] = error_count
    report_data["summary"]["total_amount_thb"] = round(report_data["summary"]["total_amount_thb"], 2)
    
    # Save comprehensive report
    report_path = r'C:\Users\peerapong\invoice-reader-app\google_invoice_comprehensive_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n" + "="*80)
    print("FINAL GOOGLE INVOICE PROCESSING REPORT")
    print("="*80)
    print(f"Total Files: {len(google_files)}")
    print(f"Successful: {successful_count}")
    print(f"Errors: {error_count}")
    print(f"Total Records: {report_data['summary']['total_records']}")
    print(f"  - Campaigns: {report_data['summary']['campaign_records']}")
    print(f"  - Refunds: {report_data['summary']['refund_records']}")
    print(f"  - Fees: {report_data['summary']['fee_records']}")
    print(f"Total Amount: {report_data['summary']['total_amount_thb']:,.2f} THB")
    print(f"\nComprehensive report saved to: {report_path}")
    
    if error_count > 0:
        print(f"\nError Files ({error_count}):")
        for error_file in report_data["error_files"][:10]:  # Show first 10 errors
            print(f"  - {error_file['filename']}: {error_file['error'][:60]}...")

if __name__ == "__main__":
    test_all_google_invoices()