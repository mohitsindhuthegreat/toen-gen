#!/usr/bin/env python3
"""
Quick test to generate tokens and test like feature
"""

import json
import time
import asyncio
from utils.token_generator import TokenGenerator
from utils.like_service import LikeService
from flask_caching import Cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    # Setup
    cache = Cache(config={'CACHE_TYPE': 'simple'})
    token_generator = TokenGenerator(cache=cache)
    like_service = LikeService()
    
    # Load credentials
    with open('ind.json', 'r') as f:
        credentials = json.load(f)
    
    successful_tokens = []
    
    # Generate tokens for first 5 credentials
    logger.info("Generating tokens for first 5 credentials...")
    
    for i, credential in enumerate(credentials[:5]):
        guest_info = credential.get('guest_account_info', {})
        uid = guest_info.get('com.garena.msdk.guest_uid')
        password = guest_info.get('com.garena.msdk.guest_password')
        
        if uid and password:
            logger.info(f"Processing UID: {uid}")
            result = token_generator.generate_token(uid, password)
            
            if result and result.get('status') == 'success':
                token_data = {
                    'uid': uid,
                    'token': result.get('token'),
                    'server': 'IND'
                }
                successful_tokens.append(token_data)
                logger.info(f"✓ Token generated for UID: {uid}")
            else:
                logger.warning(f"Failed to generate token for UID: {uid}")
        
        time.sleep(0.5)  # Small delay
    
    # Save successful tokens
    if successful_tokens:
        with open('ind_tokens_success.json', 'w') as f:
            json.dump(successful_tokens, f, indent=2)
        logger.info(f"Saved {len(successful_tokens)} tokens to ind_tokens_success.json")
        
        # Test like feature
        target_uid = "6780791579"
        logger.info(f"Testing like feature for target UID: {target_uid}")
        
        try:
            result = await like_service.process_like_request(target_uid, 'IND')
            logger.info(f"Like result: {result}")
            
            if result and result.get('status') == 'success':
                logger.info("✓ Like feature working successfully!")
            else:
                logger.warning(f"Like feature failed: {result}")
                
        except Exception as e:
            logger.error(f"Error testing like feature: {e}")
    
    else:
        logger.error("No tokens generated successfully")

if __name__ == "__main__":
    asyncio.run(main())