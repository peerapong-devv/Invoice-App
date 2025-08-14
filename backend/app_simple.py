from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import fitz  # PyMuPDF
from datetime import datetime
import tempfile
import traceback

# Import parsers
from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed
from google_parser_professional import parse_google_invoice
from facebook_parser_complete import parse_facebook_invoice

app = Flask(__name__)
CORS(app, 
     origins=["*"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type"],
     supports_credentials=False)

@app.route('/')
def index():
    return jsonify({
        'message': 'Invoice Reader API',
        'status': 'Running',
        'endpoints': {
            'health': '/api/health',
            'process': '/api/process-invoices (POST)',
            'export': '/api/export-csv (POST)'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Invoice Reader API is running'
    })

@app.route('/api/process-invoices', methods=['POST', 'OPTIONS'])
def process_invoices():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'message': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        
        # Initialize report
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_files': len(files),
            'summary': {
                'by_platform': {},
                'overall': {
                    'total_amount': 0,
                    'total_items': 0,
                    'files_processed': 0
                }
            },
            'files': {}
        }
        
        # Process each file
        for file in files:
            if file.filename and file.filename.endswith('.pdf'):
                # Save temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    file.save(tmp.name)
                    
                    try:
                        # Extract text
                        doc = fitz.open(tmp.name)
                        text_content = ""
                        for page in doc:
                            text_content += page.get_text()
                        doc.close()
                        
                        # Determine platform and parse
                        filename = file.filename
                        platform = None
                        records = []
                        
                        # Check filename pattern first
                        if filename.startswith('5'):
                            platform = 'Google'
                            records = parse_google_invoice(text_content, tmp.name)
                        elif filename.startswith('THTT'):
                            platform = 'TikTok'
                            records = parse_tiktok_invoice_detailed(text_content, filename)
                        elif filename.startswith('24'):
                            platform = 'Facebook'
                            records = parse_facebook_invoice(text_content, filename)
                        else:
                            platform = 'Unknown'
                            records = []
                        
                        # Process records
                        file_total = sum(record.get('amount', 0) for record in records)
                        
                        # Update platform summary
                        if platform not in report['summary']['by_platform']:
                            report['summary']['by_platform'][platform] = {
                                'total_amount': 0,
                                'total_items': 0,
                                'files': 0,
                                'average_items_per_file': 0
                            }
                        
                        report['summary']['by_platform'][platform]['total_amount'] += file_total
                        report['summary']['by_platform'][platform]['total_items'] += len(records)
                        report['summary']['by_platform'][platform]['files'] += 1
                        
                        # Update overall summary
                        report['summary']['overall']['total_amount'] += file_total
                        report['summary']['overall']['total_items'] += len(records)
                        report['summary']['overall']['files_processed'] += 1
                        
                        # Store file info
                        report['files'][filename] = {
                            'platform': platform,
                            'invoice_type': 'AP' if records and any(r.get('agency') == 'pk' for r in records) else 'Non-AP',
                            'total_amount': file_total,
                            'items_count': len(records),
                            'items': records
                        }
                        
                    finally:
                        os.unlink(tmp.name)
        
        # Calculate averages
        for platform_data in report['summary']['by_platform'].values():
            if platform_data['files'] > 0:
                platform_data['average_items_per_file'] = round(
                    platform_data['total_items'] / platform_data['files'], 2
                )
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {report["summary"]["overall"]["files_processed"]} files',
            'data': report
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'details': traceback.format_exc()
        }), 500

@app.route('/api/export-csv', methods=['POST'])
def export_csv():
    import csv
    import io
    from flask import send_file
    
    try:
        report = request.json
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'filename', 'platform', 'invoice_type', 'invoice_number',
            'line_number', 'description', 'amount', 'agency',
            'project_id', 'project_name', 'campaign_id', 'objective', 'period'
        ])
        
        # Data
        for filename, file_data in report['files'].items():
            for item in file_data['items']:
                writer.writerow([
                    filename,
                    item.get('platform', ''),
                    item.get('invoice_type', ''),
                    item.get('invoice_number', ''),
                    item.get('line_number', ''),
                    item.get('description', ''),
                    item.get('amount', 0),
                    item.get('agency', ''),
                    item.get('project_id', ''),
                    item.get('project_name', ''),
                    item.get('campaign_id', ''),
                    item.get('objective', ''),
                    item.get('period', '')
                ])
        
        # Convert to bytes
        output.seek(0)
        csv_bytes = '\ufeff' + output.getvalue()
        
        return send_file(
            io.BytesIO(csv_bytes.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'invoice_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)