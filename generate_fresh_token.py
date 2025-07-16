#!/usr/bin/env python3
"""
Generate a fresh token for testing
"""
import json
from utils.token_generator import TokenGenerator

def generate_fresh_token():
    """Generate a fresh token from credentials"""
    
    # Load credentials
    try:
        with open('ind.json', 'r') as f:
            credentials = json.load(f)
    except FileNotFoundError:
        print("❌ No credentials file found")
        return None
    
    if not credentials:
        print("❌ No credentials available")
        return None
    
    # Take the first credential
    cred = credentials[0]
    guest_info = cred.get('guest_account_info', {})
    uid = guest_info.get('com.garena.msdk.guest_uid')
    password = guest_info.get('com.garena.msdk.guest_password')
    
    if not uid or not password:
        print("❌ Invalid credential format")
        return None
    
    print(f"Generating fresh token for UID: {uid}")
    
    # Generate token
    token_generator = TokenGenerator()
    
    try:
        result = token_generator.generate_token(uid, password)
        
        if result and result.get('success'):
            token = result['token']
            print(f"✓ Fresh token generated successfully!")
            print(f"Token: {token[:50]}...")
            
            # Save the fresh token
            fresh_token_data = {
                "uid": uid,
                "token": token,
                "server": "IND",
                "generated_at": "2025-07-16"
            }
            
            with open('fresh_token.json', 'w') as f:
                json.dump(fresh_token_data, f, indent=2)
            
            print("✓ Fresh token saved to fresh_token.json")
            return token
        else:
            print(f"❌ Token generation failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating token: {str(e)}")
        return None

if __name__ == "__main__":
    generate_fresh_token()