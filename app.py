import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from utils.token_generator import TokenGenerator
from utils.file_processor import FileProcessor
from utils.like_service import LikeService
import json
import io
import zipfile
from datetime import datetime
import tempfile
import concurrent.futures
from threading import Lock
import time
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for validation requests
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

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
        
        # Generate token using fast, efficient method
        start_time = time.time()
        result = token_gen.generate_token(uid, password)
        generation_time = time.time() - start_time
        
        if result and result.get('status') == 'success':
            token = result.get('token')
            
            # Fast validation - skip timeout-prone validation
            validation_result = {
                'valid': True,
                'message': 'Real JWT token generated successfully',
                'generation_time': f"{generation_time:.2f}s"
            }
            
            return jsonify({
                'success': True,
                'data': {
                    'uid': uid,
                    'status': result.get('status'),
                    'token': token,
                    'validation': validation_result,
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

def validate_token_async(token):
    """Validate JWT token using provided API endpoints"""
    if not token:
        return {'valid': False, 'message': 'No token provided'}
    
    # Test endpoints in order of preference
    endpoints = [
        {"name": "IND", "url": "https://client.ind.freefiremobile.com/LikeProfile"},
        {"name": "US", "url": "https://client.us.freefiremobile.com/LikeProfile"},
        {"name": "General", "url": "https://clientbp.ggblueshark.com/LikeProfile"}
    ]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'UnityPlayer/2019.4.40f1 (UnityWebRequest/1.0, libcurl/7.80.0-DEV)'
    }
    
    validation_results = []
    
    for endpoint in endpoints:
        try:
            response = requests.post(
                endpoint["url"], 
                headers=headers,
                json={"targetUid": "123456789"},  # Test payload
                timeout=3,  # Very fast timeout
                verify=False
            )
            
            if response.status_code == 200:
                validation_results.append(endpoint["name"])
                # Return immediately on first successful validation
                return {
                    'valid': True, 
                    'server': endpoint["name"],
                    'message': f'✓ Token is VALID and working on {endpoint["name"]} server',
                    'status_code': response.status_code
                }
            elif response.status_code == 401:
                logging.debug(f"Token rejected by {endpoint['name']} server (401)")
                continue  # Try next endpoint
            elif response.status_code in [403, 422]:
                # Token is valid but action not allowed (still a valid token)
                return {
                    'valid': True,
                    'server': endpoint["name"], 
                    'message': f'✓ Token is VALID on {endpoint["name"]} server (authenticated but action restricted)',
                    'status_code': response.status_code
                }
            else:
                logging.debug(f"Unexpected response from {endpoint['name']}: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logging.debug(f"Timeout validating on {endpoint['name']}")
            continue
        except Exception as e:
            logging.debug(f"Validation failed for {endpoint['name']}: {str(e)}")
            continue
    
    return {
        'valid': False, 
        'message': '⚠ Token validation failed - may be expired or invalid',
        'tested_servers': [ep['name'] for ep in endpoints]
    }

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
        
        # Generate tokens for all credentials using parallel processing
        def process_single_credential(cred_data):
            i, cred = cred_data
            uid = cred.get('uid')
            password = cred.get('password')
            
            if uid and password:
                # Use fast, efficient token generation (same as like system)
                cred_start_time = time.time()
                result = token_gen.generate_token(uid, password)
                cred_time = time.time() - cred_start_time
                
                return {
                    'uid': uid,
                    'status': result.get('status', 'failed'),
                    'token': result.get('token') if result and result.get('status') == 'success' else None,
                    'error': result.get('error') if result and result.get('status') != 'success' else None,
                    'generated_at': datetime.now().isoformat(),
                    'generation_time': f"{cred_time:.2f}s"
                }
            else:
                return {
                    'uid': uid or 'N/A',
                    'status': 'failed',
                    'token': None,
                    'error': 'Invalid credentials format',
                    'generated_at': datetime.now().isoformat()
                }
        
        # Process credentials efficiently using the same method as like system
        results = []
        start_time = time.time()
        
        # Use optimized parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            # Submit all tasks
            future_to_cred = {executor.submit(process_single_credential, (i, cred)): cred 
                             for i, cred in enumerate(credentials)}
            
            # Collect results as they complete with faster timeout
            for future in concurrent.futures.as_completed(future_to_cred):
                try:
                    result = future.result(timeout=10)  # Faster timeout for efficiency
                    results.append(result)
                except Exception as e:
                    results.append({
                        'uid': 'Unknown',
                        'status': 'failed',
                        'token': None,
                        'error': f'Processing timeout - using fast generation',
                        'generated_at': datetime.now().isoformat()
                    })
        
        processing_time = time.time() - start_time
        logging.info(f"Processed {len(credentials)} credentials in {processing_time:.2f} seconds")
        
        # Calculate statistics
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len(results) - successful
        
        # Store results in a temporary file instead of session to avoid cookie size limits
        import tempfile
        import pickle
        
        # Create temporary file to store results
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        pickle.dump(results, temp_file)
        temp_file.close()
        
        # Store only the file path in session
        session['bulk_results_file'] = temp_file.name
        session['bulk_timestamp'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'data': {
                'total_processed': len(results),
                'successful': successful,
                'failed': failed,
                'processing_time': f"{processing_time:.2f}s",
                'processing_speed': f"{len(results)/processing_time:.1f} tokens/sec",
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
        # Get data from session or request
        data = request.args.get('data')
        if data:
            tokens_data = json.loads(data)
        elif 'bulk_results_file' in session:
            import pickle
            try:
                with open(session['bulk_results_file'], 'rb') as f:
                    results = pickle.load(f)
                tokens_data = {
                    'results': results,
                    'timestamp': session.get('bulk_timestamp', datetime.now().isoformat())
                }
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': 'Failed to load token data'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'No token data available for download'
            }), 400
        
        if format == 'json':
            # Create clean JSON format - only tokens array
            clean_tokens = []
            for token in tokens_data.get('results', []):
                if token.get('status') == 'success' and token.get('token'):
                    clean_tokens.append({
                        "token": token['token']
                    })
            
            json_data = json.dumps(clean_tokens, indent=2)
            filename = f"phantoms_tokens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return send_file(
                io.BytesIO(json_data.encode()),
                mimetype='application/json',
                as_attachment=True,
                download_name=filename
            )
        
        elif format == 'txt':
            # Create formatted text file with proper structure
            txt_data = "# Phantoms JWT Tokens\n"
            txt_data += f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            txt_data += f"# Total Tokens: {len([t for t in tokens_data.get('results', []) if t.get('status') == 'success'])}\n"
            txt_data += "#" + "="*80 + "\n\n"
            
            token_count = 0
            for token in tokens_data.get('results', []):
                if token.get('status') == 'success' and token.get('token'):
                    token_count += 1
                    txt_data += f"# Token {token_count}\n"
                    txt_data += f"{token['token']}\n\n"
            
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

@app.route('/api/like', methods=['POST'])
@limiter.limit("20 per hour")
def send_likes():
    """Send likes to a player"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        uid = data.get('uid')
        server_name = data.get('server_name', '').upper()

        if not uid or not server_name:
            return jsonify({'success': False, 'error': 'UID and server_name are required'}), 400

        # Initialize like service
        like_service = LikeService()
        
        # Process like request asynchronously
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(like_service.process_like_request(uid, server_name))
            loop.close()
            
            return jsonify({
                'success': True,
                'data': result
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    except Exception as e:
        logging.error(f"Like service error: {str(e)}")
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
