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
        simple_patterns = [
            r'(?:uid|UID):\s*([^\s,;|]+)\s*(?:pass|password|PASS|PASSWORD):\s*([^\s,;|]+)',
            r'(?:uid|UID)\s*=\s*([^\s,;|]+)\s*(?:pass|password|PASS|PASSWORD)\s*=\s*([^\s,;|]+)',
            r'([^\s,;|]+)\s*:\s*([^\s,;|]+)',  # Simple uid:password format
            r'([^\s,;|]+)\s*\|\s*([^\s,;|]+)', # uid|password format
            r'([^\s,;|]+)\s*,\s*([^\s,;|]+)',  # uid,password format
        ]
        
        for pattern in simple_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                uid, password = match
                # Basic validation - UID should be numeric and password should be alphanumeric
                if uid.isdigit() and len(uid) >= 8 and len(password) >= 8:
                    credentials.append({
                        'uid': uid,
                        'password': password
                    })
        
        # Pattern for lines with UID and password separated by various delimiters
        line_patterns = [
            r'(\d{8,})[:\s|,;]+([A-F0-9a-f]{32,})',  # Hex passwords
            r'(\d{8,})[:\s|,;]+([A-Za-z0-9]{8,})',   # Alphanumeric passwords
        ]
        
        for pattern in line_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                uid, password = match
                credentials.append({
                    'uid': uid,
                    'password': password
                })
        
        # Remove duplicates
        seen = set()
        unique_credentials = []
        for cred in credentials:
            key = (cred['uid'], cred['password'])
            if key not in seen:
                seen.add(key)
                unique_credentials.append(cred)
        
        return unique_credentials
    
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
