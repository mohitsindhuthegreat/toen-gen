import base64
import json
import logging

class JWTDecoder:
    """Utility class to decode JWT tokens and extract UID information"""
    
    def __init__(self):
        pass
    
    def decode_jwt_payload(self, token):
        """Decode JWT token and extract payload information"""
        try:
            # JWT format: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (second part)
            payload = parts[1]
            
            # Add padding if needed
            while len(payload) % 4:
                payload += '='
            
            # Decode base64
            decoded_bytes = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded_bytes.decode('utf-8'))
            
            return payload_data
            
        except Exception as e:
            logging.error(f"Error decoding JWT: {str(e)}")
            return None
    
    def extract_uid_from_token(self, token):
        """Extract UID from JWT token"""
        payload = self.decode_jwt_payload(token)
        if payload:
            # Try different UID fields that might be present
            uid = payload.get('external_uid') or payload.get('uid') or payload.get('account_id')
            return str(uid) if uid else None
        return None
    
    def extract_nickname_from_token(self, token):
        """Extract nickname from JWT token"""
        payload = self.decode_jwt_payload(token)
        if payload:
            return payload.get('nickname', 'Unknown Player')
        return 'Unknown Player'
    
    def get_token_info(self, token):
        """Get comprehensive token information"""
        payload = self.decode_jwt_payload(token)
        if payload:
            return {
                'uid': payload.get('external_uid') or payload.get('uid') or payload.get('account_id'),
                'nickname': payload.get('nickname', 'Unknown Player'),
                'region': payload.get('noti_region', 'Unknown'),
                'account_id': payload.get('account_id'),
                'external_uid': payload.get('external_uid'),
                'exp': payload.get('exp'),
                'country_code': payload.get('country_code', 'Unknown')
            }
        return None