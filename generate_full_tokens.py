#!/usr/bin/env python3
"""
Generate tokens for all IND credentials and test the system
"""

import json
import time
from utils.token_generator import TokenGenerator
from flask_caching import Cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_all_tokens():
    """Generate tokens for all available credentials"""
    
    # Setup
    cache = Cache(config={'CACHE_TYPE': 'simple'})
    token_generator = TokenGenerator(cache=cache)
    
    # Load credentials
    with open('ind.json', 'r') as f:
        credentials = json.load(f)
    
    logger.info(f"Starting token generation for {len(credentials)} credentials...")
    
    successful_tokens = []
    failed_tokens = []
    
    # Process in batches
    batch_size = 20
    for i in range(0, len(credentials), batch_size):
        batch = credentials[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}: credentials {i+1}-{min(i+batch_size, len(credentials))}")
        
        for j, credential in enumerate(batch):
            guest_info = credential.get('guest_account_info', {})
            uid = guest_info.get('com.garena.msdk.guest_uid')
            password = guest_info.get('com.garena.msdk.guest_password')
            
            if uid and password:
                try:
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
                        failed_tokens.append({'uid': uid, 'error': result.get('error', 'Unknown error')})
                        logger.warning(f"Failed to generate token for UID: {uid}")
                        
                except Exception as e:
                    failed_tokens.append({'uid': uid, 'error': str(e)})
                    logger.error(f"Error processing UID {uid}: {e}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.3)
        
        # Longer delay between batches
        if i + batch_size < len(credentials):
            logger.info("Waiting 3 seconds before next batch...")
            time.sleep(3)
    
    # Save results
    logger.info(f"Token generation complete. Successful: {len(successful_tokens)}, Failed: {len(failed_tokens)}")
    
    # Save to both locations
    with open('tokens/ind.json', 'w') as f:
        json.dump(successful_tokens, f, indent=2)
    
    with open('ind_tokens_complete.json', 'w') as f:
        json.dump({
            'successful': successful_tokens,
            'failed': failed_tokens,
            'summary': {
                'total_processed': len(credentials),
                'successful_count': len(successful_tokens),
                'failed_count': len(failed_tokens),
                'success_rate': f"{len(successful_tokens)/len(credentials)*100:.1f}%"
            }
        }, f, indent=2)
    
    logger.info(f"Tokens saved to tokens/ind.json and ind_tokens_complete.json")
    
    # Display summary
    print("\n" + "="*50)
    print("TOKEN GENERATION SUMMARY")
    print("="*50)
    print(f"Total processed: {len(credentials)}")
    print(f"Successful: {len(successful_tokens)}")
    print(f"Failed: {len(failed_tokens)}")
    print(f"Success rate: {len(successful_tokens)/len(credentials)*100:.1f}%")
    print("="*50)
    
    if successful_tokens:
        print("\nFirst 3 successful tokens:")
        for i, token in enumerate(successful_tokens[:3]):
            print(f"  {i+1}. UID: {token['uid']}")
            print(f"     Token: {token['token'][:60]}...")
            print()

if __name__ == "__main__":
    generate_all_tokens()