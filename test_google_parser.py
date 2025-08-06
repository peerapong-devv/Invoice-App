import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import process_invoice_file
import json

def test_google_invoices():
    """Test Google invoice parser with real files"""
    
    test_files = [
        ("5298248238.pdf", "AP"),      # Google AP invoice
        ("5300646032.pdf", "Non-AP")    # Google Non-AP invoice
    ]
    
    print("=== TESTING GOOGLE INVOICE PARSER ===\n")
    
    for filename, expected_type in test_files:
        print(f"Testing {filename} (Expected: {expected_type})")
        print("-" * 60)
        
        if os.path.exists(filename):
            # Create temp upload folder
            if not os.path.exists('backend/uploads'):
                os.makedirs('backend/uploads')
            
            # Copy file to uploads folder
            import shutil
            upload_path = os.path.join('backend/uploads', filename)
            shutil.copy(filename, upload_path)
            
            # Process the invoice
            try:
                records = process_invoice_file(upload_path, filename)
                
                print(f"Found {len(records)} line items\n")
                
                for record in records:
                    try:
                        print(f"Line {record['line_number']}:")
                        print(f"  Platform: {record['platform']}")
                        print(f"  Type: {record['invoice_type']}")
                        print(f"  Agency: {record['agency']}")
                        print(f"  Project ID: {record['project_id']}")
                        print(f"  Project Name: {record['project_name']}")
                        print(f"  Objective: {record['objective']}")
                        print(f"  Campaign ID: {record['campaign_id']}")
                        print(f"  Total: {record['total']}")
                        desc = record['description']
                        if desc:
                            desc_preview = desc[:100] + "..." if len(desc) > 100 else desc
                            print(f"  Description: {desc_preview}")
                        else:
                            print(f"  Description: None")
                        print()
                    except UnicodeEncodeError:
                        print(f"Line {record['line_number']}: [Unicode encoding error - see JSON file for details]")
                        print()
                
                # Save results to JSON
                output_file = filename.replace('.pdf', '_parsed.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
                print(f"Results saved to: {output_file}")
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"File not found: {filename}")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_google_invoices()