import os
import sys
import uuid
import json
import threading
import webbrowser
import time
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from converter_engine import convert_pdf_to_html

# Determine base path for templates & static (PyInstaller compatibility)
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = BUNDLE_DIR

app = Flask(__name__,
            template_folder=os.path.join(BUNDLE_DIR, 'templates'),
            static_folder=os.path.join(BUNDLE_DIR, 'static'))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB max upload

# Store session metadata in memory
SESSIONS = {}

@app.before_request
def handle_options_preflight():
    if request.method == 'OPTIONS':
        res = app.make_default_options_response()
        res.headers['Access-Control-Allow-Origin'] = '*'
        res.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
        res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        return res

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'ok', 'service': 'PDF to HTML Converter Backend', 'version': '2.0'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/convert', methods=['POST'])
def convert_file():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    
    session_id = str(uuid.uuid4())[:8]
    original_filename = secure_filename(file.filename) or 'document.pdf'
    
    session_upload_dir = os.path.join(UPLOAD_FOLDER, session_id)
    session_output_dir = os.path.join(OUTPUT_FOLDER, session_id)
    os.makedirs(session_upload_dir, exist_ok=True)
    os.makedirs(session_output_dir, exist_ok=True)
    
    pdf_save_path = os.path.join(session_upload_dir, original_filename)
    file.save(pdf_save_path)
    
    try:
        result = convert_pdf_to_html(pdf_save_path, session_output_dir)
        SESSIONS[session_id] = {
            'id': session_id,
            'title': result['title'],
            'totalPages': result['totalPages'],
            'outputDir': session_output_dir,
            'continuousBookPath': result['continuousBookPath'],
            'continuousBookFilename': result['continuousBookFilename'],
            'zipPath': result['zipPath'],
            'zipFilename': result['zipFilename'],
            'data': result['data']
        }
        return jsonify({
            'success': True,
            'sessionId': session_id,
            'title': result['title'],
            'totalPages': result['totalPages'],
            'bookFilename': result['continuousBookFilename'],
            'data': result['data']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>/page/<int:page_num>')
def get_page(session_id, page_num):
    session = SESSIONS.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    pages = session['data']['pages']
    if page_num < 1 or page_num > len(pages):
        return jsonify({'error': 'Page number out of range'}), 400
    
    return jsonify(pages[page_num - 1])

@app.route('/api/session/<session_id>/download/standalone')
def download_standalone_reader(session_id):
    """
    Downloads 1 single self-contained HTML book file where all pages are stacked vertically
    so the user can scroll down and read the entire book in pure HTML+CSS.
    """
    session = SESSIONS.get(session_id)
    if not session or not os.path.exists(session.get('continuousBookPath', '')):
        return jsonify({'error': 'Book file not found'}), 404
    
    return send_file(
        session['continuousBookPath'],
        as_attachment=True,
        download_name=session['continuousBookFilename']
    )

@app.route('/api/session/<session_id>/download/zip')
def download_zip(session_id):
    session = SESSIONS.get(session_id)
    if not session or not os.path.exists(session.get('zipPath', '')):
        return jsonify({'error': 'ZIP package not found'}), 404
    
    return send_file(
        session['zipPath'],
        as_attachment=True,
        download_name=session['zipFilename']
    )

@app.route('/outputs/<session_id>/<path:filepath>')
def serve_output_file(session_id, filepath):
    session_dir = os.path.join(OUTPUT_FOLDER, session_id)
    return send_from_directory(session_dir, filepath)

def open_browser(port):
    time.sleep(1.5)
    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    print("=" * 70)
    print("  [PDF to HTML/CSS Converter WebApp Studio Started]")
    print(f"  Access URL: http://0.0.0.0:{port}")
    print("=" * 70)
    if not os.environ.get('PORT'):
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    app.run(host='0.0.0.0', port=port, debug=False)

