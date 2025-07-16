#!/usr/bin/env python3
"""
Test single token generation from IND credentials
"""

import json
import sys
from utils.token_generator import TokenGenerator
from flask_caching import Cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_token():
    """Test token generation with the first credential"""
    
    # Load credentials
    try:
        with open('ind.json', 'r') as f:
            credentials = json.load(f)
        logger.info(f"Loaded {len(credentials)} credentials")
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return
    
    if not credentials:
        logger.error("No credentials found")
        return
    
    # Setup token generator
    cache = Cache(config={'CACHE_TYPE': 'simple'})
    token_generator = TokenGenerator(cache=cache)
    
    # Test with first credential
    credential = credentials[0]
    guest_info = credential.get('guest_account_info', {})
    uid = guest_info.get('com.garena.msdk.guest_uid')
    password = guest_info.get('com.garena.msdk.guest_password')
    
    if not uid or not password:
        logger.error("Missing UID or password in first credential")
        return
    
    logger.info(f"Testing with UID: {uid}")
    logger.info(f"Password: {password[:10]}...")
    
    # Generate token
    result = token_generator.generate_token(uid, password)
    
    logger.info(f"Result: {result}")
    
    if result and result.get('status') == 'success':
        logger.info("✓ Token generation successful!")
        logger.info(f"Token: {result.get('token', 'N/A')}")
        
        # Save successful token
        token_data = {
            'uid': uid,
            'token': result.get('token'),
            'server': 'IND',
            'status': 'success'
        }
        
        with open('test_token_success.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        logger.info("Token saved to test_token_success.json")
        
    else:
        logger.error(f"Token generation failed: {result}")

if __name__ == "__main__":
    test_single_token()