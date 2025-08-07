from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import fitz  # PyMuPDF
import easyocr

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

reader = None
def get_easyocr_reader():
    global reader
    if reader is None:
        reader = easyocr.Reader(['en', 'th'], gpu=False)
    return reader

def create_final_unified_template():
    return {
        "platform": None, "invoice_type": None,
        "invoice_id": None, "line_number": None, "agency": None,
        "project_id": None, "project_name": None, "objective": None,
        "period": None, "campaign_id": None, "total": None, "description": None,
    }

def parse_invoice_text(text_content: str, filename: str, file_path: str = None):
    # Detect platform and use appropriate parser
    if filename.startswith('THTT') or "tiktok" in text_content.lower() or "bytedance" in text_content.lower():
        from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed
        records = parse_tiktok_invoice_detailed(text_content, filename)
    elif filename.startswith('5') or ("google" in text_content.lower() and "ads" in text_content.lower()):
        from google_parser_complete import parse_google_invoice
        records = parse_google_invoice(text_content, filename)
    elif filename.startswith('24') or "facebook" in text_content.lower() or "meta" in text_content.lower():
        from facebook_parser_complete import parse_facebook_invoice
        records = parse_facebook_invoice(text_content, filename)
    else:
        return [{"platform": "Unknown", "filename": filename, "total": 0}]
    
    # If no records found, return unknown
    if not records:
        return [{"platform": "Unknown", "filename": filename, "total": 0}]
    
    # Normalize records to ensure template compliance
    from fixed_template_handler import normalize_record
    normalized_records = []
    for record in records:
        normalized = normalize_record(record)
        normalized_records.append(normalized)
    
    return normalized_records

def get_base_fields(text_content: str):
    base_data = {}
    match = re.search(r"(?:Invoice number|Invoice No\.|Invoice #:|หมายเลขใบแจ้งหนี้:)\s*([\w-]+)", text_content, re.IGNORECASE)
    if match:
        base_data["invoice_id"] = match.group(1).strip()
    return base_data

# Remove unused parser functions since we're importing the working parsers directly

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            # Extract text from PDF
            with fitz.open(file_path) as doc:
                text_content = ""
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text_content += page.get_text()
            
            # Parse the invoice
            records = parse_invoice_text(text_content, filename, file_path)
            
            return jsonify({'records': records, 'success': True})
            
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
        finally:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    return jsonify({'error': 'Invalid file format'}), 400

if __name__ == '__main__':
    app.run(debug=True)