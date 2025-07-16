import json
import re
import logging
from werkzeug.utils import secure_filename

class FileProcessor:
    def __init__(self):
        self.allowed_extensions = {'txt', 'json'}
        
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def extract_credentials_from_text(self, content):
        """Extract UID and password from text content"""
        credentials = []
        
        # Pattern for JSON format like in the uploaded files
        json_pattern = r'\{"guest_account_info":\s*\{\s*"com\.garena\.msdk\.guest_uid":\s*"([^"]+)",\s*"com\.garena\.msdk\.guest_password":\s*"([^"]+)"\s*\}\s*\}'
        
        # Find all JSON matches
        json_matches = re.findall(json_pattern, content)
        for match in json_matches:
            uid, password = match
            credentials.append({
                'uid': uid,
                'password': password
            })
        
        # Pattern for simple UID:PASSWORD format
        simple_pattern = r'(?:uid|UID):\s*([^\s]+)\s*(?:pass|password|PASS|PASSWORD):\s*([^\s]+)'
        simple_matches = re.findall(simple_pattern, content, re.IGNORECASE)
        for match in simple_matches:
            uid, password = match
            credentials.append({
                'uid': uid,
                'password': password
            })
        
        # Pattern for lines with UID and password separated by various delimiters
        line_pattern = r'(\d{10,})[:\s|,;]+([A-F0-9]{64})'
        line_matches = re.findall(line_pattern, content)
        for match in line_matches:
            uid, password = match
            credentials.append({
                'uid': uid,
                'password': password
            })
        
        return credentials
    
    def extract_credentials_from_json(self, content):
        """Extract UID and password from JSON content"""
        credentials = []
        
        try:
            # Try to parse as JSON array
            data = json.loads(content)
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # Check for guest_account_info format
                        if 'guest_account_info' in item:
                            info = item['guest_account_info']
                            uid = info.get('com.garena.msdk.guest_uid')
                            password = info.get('com.garena.msdk.guest_password')
                            if uid and password:
                                credentials.append({
                                    'uid': uid,
                                    'password': password
                                })
                        # Check for direct uid/password format
                        elif 'uid' in item and 'password' in item:
                            credentials.append({
                                'uid': item['uid'],
                                'password': item['password']
                            })
            
            elif isinstance(data, dict):
                # Single object
                if 'guest_account_info' in data:
                    info = data['guest_account_info']
                    uid = info.get('com.garena.msdk.guest_uid')
                    password = info.get('com.garena.msdk.guest_password')
                    if uid and password:
                        credentials.append({
                            'uid': uid,
                            'password': password
                        })
                elif 'uid' in data and 'password' in data:
                    credentials.append({
                        'uid': data['uid'],
                        'password': data['password']
                    })
        
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract from text
            credentials = self.extract_credentials_from_text(content)
        
        return credentials
    
    def process_file(self, file):
        """Process uploaded file and extract credentials"""
        try:
            if not file or not self.allowed_file(file.filename):
                return []
            
            # Read file content
            content = file.read().decode('utf-8')
            
            # Determine file type and extract credentials
            if file.filename.lower().endswith('.json'):
                credentials = self.extract_credentials_from_json(content)
            else:
                credentials = self.extract_credentials_from_text(content)
            
            # Remove duplicates
            unique_credentials = []
            seen = set()
            for cred in credentials:
                key = (cred['uid'], cred['password'])
                if key not in seen:
                    seen.add(key)
                    unique_credentials.append(cred)
            
            logging.info(f"Extracted {len(unique_credentials)} unique credentials from {file.filename}")
            return unique_credentials
            
        except Exception as e:
            logging.error(f"Error processing file {file.filename}: {str(e)}")
            return []
