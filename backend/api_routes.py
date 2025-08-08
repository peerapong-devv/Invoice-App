#!/usr/bin/env python3
"""API routes for invoice processing"""

from flask import Blueprint, request, jsonify, send_file
import os
import tempfile
import fitz
from datetime import datetime
import json
import csv
import io
import traceback
import sys
import time

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import parsers with error handling
try:
    from final_improved_tiktok_parser_v2 import parse_tiktok_invoice_detailed
    from google_parser_professional import parse_google_invoice
    from facebook_parser_complete import parse_facebook_invoice
    print("Parsers imported successfully")
except ImportError as e:
    print(f"Error importing parsers: {e}")
    traceback.print_exc()

api = Blueprint('api', __name__)

@api.route('/test-upload', methods=['POST'])
def test_upload():
    """Test file upload endpoint"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files in request'}), 400
        
        files = request.files.getlist('files')
        file_info = []
        
        for file in files:
            file_info.append({
                'filename': file.filename,
                'content_type': file.content_type,
                'size': len(file.read())
            })
            file.seek(0)  # Reset file pointer
        
        return jsonify({
            'success': True,
            'files_received': len(files),
            'file_info': file_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    parsers_status = {
        'tiktok': False,
        'google': False,
        'facebook': False
    }
    
    try:
        # Test if parsers can be called
        if 'parse_tiktok_invoice_detailed' in globals():
            parsers_status['tiktok'] = True
        if 'parse_google_invoice' in globals():
            parsers_status['google'] = True
        if 'parse_facebook_invoice' in globals():
            parsers_status['facebook'] = True
    except Exception as e:
        print(f"Error checking parsers: {e}")
    
    return jsonify({
        'status': 'healthy',
        'message': 'Invoice Reader API is running',
        'parsers': parsers_status,
        'python_version': sys.version
    })

@api.route('/process-invoices-simple', methods=['POST'])
def process_invoices_simple():
    """Simple test endpoint for invoice processing"""
    try:
        # Check if we have files
        if 'files' not in request.files:
            return jsonify({'error': 'No files in request'}), 400
        
        files = request.files.getlist('files')
        
        # Just try to read the first file
        if files:
            file = files[0]
            
            # Save and process
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                file.save(tmp.name)
                
                # Try to open with PyMuPDF
                try:
                    import fitz
                    doc = fitz.open(tmp.name)
                    page_count = len(doc)
                    text = doc[0].get_text() if page_count > 0 else ""
                    doc.close()
                    
                    os.unlink(tmp.name)
                    
                    return jsonify({
                        'success': True,
                        'filename': file.filename,
                        'pages': page_count,
                        'text_length': len(text),
                        'first_100_chars': text[:100]
                    })
                except Exception as e:
                    os.unlink(tmp.name)
                    return jsonify({
                        'error': 'PyMuPDF error',
                        'details': str(e)
                    }), 500
        
        return jsonify({'error': 'No files provided'}), 400
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500

@api.route('/process-invoices', methods=['POST', 'OPTIONS'])
def process_invoices():
    """Process uploaded invoice PDF files"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        return '', 200
    
    try:
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No files uploaded'
            }), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({
                'success': False,
                'message': 'No files selected'
            }), 400
        
        # Initialize report structure
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
                print(f"Processing file: {file.filename}")
                # Save temporary file
                temp_dir = tempfile.gettempdir()
                temp_filename = os.path.join(temp_dir, f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file.save(temp_filename)
                print(f"Saved to temp file: {temp_filename}")
                
                # Add a small delay to ensure file is fully written and handle is released
                time.sleep(0.1)
                
                try:
                    # Extract text from PDF
                    doc = fitz.open(temp_filename)
                    text_content = ""
                    for page in doc:
                        text_content += page.get_text()
                    doc.close()  # Important: close the document
                    print(f"Extracted {len(text_content)} characters from PDF")
                    
                    # Determine platform and parse
                    filename = file.filename
                    platform = None
                    records = []
                    
                    # Priority: Check filename pattern first
                    if filename.startswith('5'):
                        platform = 'Google'
                        records = parse_google_invoice(text_content, temp_filename)
                    elif filename.startswith('THTT'):
                        platform = 'TikTok'
                        records = parse_tiktok_invoice_detailed(text_content, filename)
                    elif filename.startswith('24'):
                        platform = 'Facebook'
                        records = parse_facebook_invoice(text_content, filename)
                    # Fallback to content checking
                    elif "tiktok" in text_content.lower() and "facebook" not in text_content.lower():
                        platform = 'TikTok'
                        records = parse_tiktok_invoice_detailed(text_content, filename)
                    elif "facebook" in text_content.lower() or "meta" in text_content.lower():
                        platform = 'Facebook'
                        records = parse_facebook_invoice(text_content, filename)
                    elif "google" in text_content.lower():
                        platform = 'Google'
                        records = parse_google_invoice(text_content, temp_filename)
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
                    
                    # Determine invoice type
                    invoice_type = 'Unknown'
                    if records:
                        if any(r.get('agency') == 'pk' for r in records):
                            invoice_type = 'AP'
                        else:
                            invoice_type = 'Non-AP'
                    
                    # Store file info
                    report['files'][filename] = {
                        'platform': platform,
                        'invoice_type': invoice_type,
                        'total_amount': file_total,
                        'items_count': len(records),
                        'items': records
                    }
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_filename):
                        os.unlink(temp_filename)
        
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
        error_details = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"Error processing invoices: {error_details}")
        return jsonify({
            'success': False,
            'message': f'Error processing invoices: {str(e)}',
            'details': error_details
        }), 500

@api.route('/export-csv', methods=['POST'])
def export_csv():
    """Export invoice report to CSV"""
    try:
        report = request.json
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'filename',
            'platform',
            'invoice_type',
            'invoice_number',
            'line_number',
            'description',
            'amount',
            'agency',
            'project_id',
            'project_name',
            'campaign_id',
            'objective',
            'period'
        ])
        
        # Write data
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
        
        # Convert to bytes with UTF-8 BOM for Excel
        output.seek(0)
        csv_bytes = '\ufeff' + output.getvalue()  # Add BOM for Excel
        
        return send_file(
            io.BytesIO(csv_bytes.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'invoice_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        print(f"Error exporting CSV: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error exporting CSV: {str(e)}'
        }), 500