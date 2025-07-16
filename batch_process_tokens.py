#!/usr/bin/env python3
"""
Batch process IND credentials to generate real tokens
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

class BatchTokenProcessor:
    def __init__(self):
        self.cache = Cache(config={'CACHE_TYPE': 'simple'})
        self.token_generator = TokenGenerator(cache=self.cache)
        self.like_service = LikeService()
        self.successful_tokens = []
        self.failed_tokens = []
        
    def load_credentials(self, file_path='ind.json'):
        """Load credentials from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} credentials from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return []
    
    def extract_uid_password(self, credential_data):
        """Extract UID and password from credential data"""
        try:
            guest_info = credential_data.get('guest_account_info', {})
            uid = guest_info.get('com.garena.msdk.guest_uid')
            password = guest_info.get('com.garena.msdk.guest_password')
            
            if uid and password:
                return uid, password
            else:
                logger.warning(f"Missing UID or password in credential: {credential_data}")
                return None, None
        except Exception as e:
            logger.error(f"Error extracting credentials: {e}")
            return None, None
    
    def process_single_credential(self, credential_data, retry_count=2):
        """Process a single credential with retry logic"""
        uid, password = self.extract_uid_password(credential_data)
        
        if not uid or not password:
            return None
            
        for attempt in range(retry_count):
            try:
                logger.info(f"Processing UID: {uid} (attempt {attempt + 1}/{retry_count})")
                
                # Generate token
                result = self.token_generator.generate_token(uid, password)
                
                if result and result.get('status') == 'success':
                    token_data = {
                        'uid': uid,
                        'token': result.get('token'),
                        'server': 'IND',
                        'generated_at': time.time(),
                        'attempt': attempt + 1
                    }
                    self.successful_tokens.append(token_data)
                    logger.info(f"✓ Successfully generated token for UID: {uid}")
                    return token_data
                else:
                    logger.warning(f"Failed to generate token for UID: {uid} - {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error processing UID {uid}: {e}")
                
            # Wait before retry
            if attempt < retry_count - 1:
                time.sleep(0.5)
                
        # If all attempts failed
        self.failed_tokens.append({
            'uid': uid,
            'error': 'Max retry attempts reached',
            'attempts': retry_count
        })
        return None
    
    def process_batch(self, num_tokens=10):
        """Process a batch of credentials"""
        credentials = self.load_credentials()
        
        if not credentials:
            logger.error("No credentials loaded")
            return
            
        logger.info(f"Processing first {num_tokens} credentials")
        
        # Process only the first num_tokens credentials
        for i, credential in enumerate(credentials[:num_tokens]):
            logger.info(f"Processing credential {i+1}/{num_tokens}")
            
            result = self.process_single_credential(credential)
            
            # Add delay between requests to avoid rate limiting
            if i < num_tokens - 1:  # Don't delay after the last one
                time.sleep(0.8)
        
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save successful and failed tokens to files"""
        # Save successful tokens
        if self.successful_tokens:
            with open('ind_tokens_success.json', 'w') as f:
                json.dump(self.successful_tokens, f, indent=2)
            logger.info(f"Saved {len(self.successful_tokens)} successful tokens to ind_tokens_success.json")
        
        # Save failed tokens
        if self.failed_tokens:
            with open('ind_tokens_failed.json', 'w') as f:
                json.dump(self.failed_tokens, f, indent=2)
            logger.info(f"Saved {len(self.failed_tokens)} failed tokens to ind_tokens_failed.json")
    
    def print_summary(self):
        """Print processing summary"""
        total = len(self.successful_tokens) + len(self.failed_tokens)
        success_rate = (len(self.successful_tokens) / total * 100) if total > 0 else 0
        
        logger.info("="*50)
        logger.info("PROCESSING SUMMARY")
        logger.info("="*50)
        logger.info(f"Total processed: {total}")
        logger.info(f"Successful: {len(self.successful_tokens)}")
        logger.info(f"Failed: {len(self.failed_tokens)}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info("="*50)
        
        if self.successful_tokens:
            logger.info("Sample successful tokens:")
            for i, token in enumerate(self.successful_tokens[:3]):
                logger.info(f"  {i+1}. UID: {token['uid']} - Token: {token['token'][:50]}...")
    
    async def test_like_feature(self, target_uid="6780791579"):
        """Test the like feature with generated tokens"""
        if not self.successful_tokens:
            logger.error("No successful tokens available for like testing")
            return
        
        logger.info(f"Testing like feature for target UID: {target_uid}")
        
        # Use first successful token for testing
        test_token = self.successful_tokens[0]
        logger.info(f"Using token from UID: {test_token['uid']}")
        
        try:
            result = await self.like_service.process_like_request(target_uid, 'IND')
            logger.info(f"Like result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error testing like feature: {e}")
            return None

def main():
    processor = BatchTokenProcessor()
    
    # Process first 10 credentials
    processor.process_batch(num_tokens=10)
    
    # Test like feature if we have successful tokens
    if processor.successful_tokens:
        logger.info("Testing like feature...")
        result = asyncio.run(processor.test_like_feature())
        if result:
            logger.info(f"Like feature test result: {result}")

if __name__ == "__main__":
    main()