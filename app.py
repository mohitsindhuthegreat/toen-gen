import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from utils.token_generator import TokenGenerator
from utils.file_processor import FileProcessor
import json
import io
import zipfile
from datetime import datetime
import tempfile

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "phantoms-jwt-secret-key-2024")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure cache
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 25200})

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize token generator
token_gen = TokenGenerator(cache)
file_processor = FileProcessor()

@app.route('/')
def index():
    """Main page with token generation interface"""
    return render_template('index.html')

@app.route('/api-docs')
def api_docs():
    """API documentation page"""
    return render_template('api_docs.html')

@app.route('/api/token', methods=['POST'])
@limiter.limit("10 per minute")
def generate_single_token():
    """Generate a single JWT token"""
    try:
        data = request.get_json()
        if not data or 'uid' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'error': 'UID and password are required'
            }), 400
        
        uid = data['uid']
        password = data['password']
        
        # Validate input
        if not uid or not password:
            return jsonify({
                'success': False,
                'error': 'UID and password cannot be empty'
            }), 400
        
        # Generate token
        result = token_gen.generate_token(uid, password)
        
        if result and result.get('status') == 'success':
            return jsonify({
                'success': True,
                'data': {
                    'uid': uid,
                    'status': result.get('status'),
                    'token': result.get('token'),
                    'generated_at': datetime.now().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Invalid credentials or token generation failed')
            }), 400
            
    except Exception as e:
        logging.error(f"Error generating token: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/bulk-token', methods=['POST'])
@limiter.limit("5 per minute")
def generate_bulk_tokens():
    """Generate multiple JWT tokens from file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Process file and extract credentials
        credentials = file_processor.process_file(file)
        
        if not credentials:
            return jsonify({
                'success': False,
                'error': 'No valid credentials found in file'
            }), 400
        
        # Generate tokens for all credentials
        results = []
        for cred in credentials:
            uid = cred.get('uid')
            password = cred.get('password')
            
            if uid and password:
                result = token_gen.generate_token(uid, password)
                results.append({
                    'uid': uid,
                    'status': result.get('status', 'failed'),
                    'token': result.get('token') if result and result.get('status') == 'success' else None,
                    'error': result.get('error') if result and result.get('status') != 'success' else None,
                    'generated_at': datetime.now().isoformat()
                })
        
        # Calculate statistics
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len(results) - successful
        
        return jsonify({
            'success': True,
            'data': {
                'total_processed': len(results),
                'successful': successful,
                'failed': failed,
                'results': results
            }
        })
        
    except Exception as e:
        logging.error(f"Error processing bulk tokens: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/download/<format>')
@limiter.limit("10 per minute")
def download_tokens(format):
    """Download generated tokens in specified format"""
    try:
        data = request.args.get('data')
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Parse the data
        tokens_data = json.loads(data)
        
        if format == 'json':
            # Create JSON file
            json_data = json.dumps(tokens_data, indent=2)
            filename = f"phantoms_tokens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return send_file(
                io.BytesIO(json_data.encode()),
                mimetype='application/json',
                as_attachment=True,
                download_name=filename
            )
        
        elif format == 'txt':
            # Create text file
            txt_data = ""
            for token in tokens_data.get('results', []):
                if token.get('status') == 'success':
                    txt_data += f"UID: {token['uid']}\n"
                    txt_data += f"Token: {token['token']}\n"
                    txt_data += f"Generated: {token['generated_at']}\n"
                    txt_data += "-" * 80 + "\n"
            
            filename = f"phantoms_tokens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            return send_file(
                io.BytesIO(txt_data.encode()),
                mimetype='text/plain',
                as_attachment=True,
                download_name=filename
            )
        
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid format. Use json or txt'
            }), 400
            
    except Exception as e:
        logging.error(f"Error downloading tokens: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded. Please try again later.'
    }), 429

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logging.error(f"Internal server error: {str(e)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
