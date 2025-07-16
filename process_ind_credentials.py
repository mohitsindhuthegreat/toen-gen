#!/usr/bin/env python3
"""
Process IND credentials file and generate real tokens
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

class IndCredentialsProcessor:
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
    
    def process_single_credential(self, credential_data, retry_count=3):
        """Process a single credential with retry logic"""
        uid, password = self.extract_uid_password(credential_data)
        
        if not uid or not password:
            return None
            
        for attempt in range(retry_count):
            try:
                logger.info(f"Processing UID: {uid} (attempt {attempt + 1}/{retry_count})")
                
                # Generate token
                result = self.token_generator.generate_token(uid, password)
                
                if result and result.get('success'):
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
                time.sleep(1)
                
        # If all attempts failed
        self.failed_tokens.append({
            'uid': uid,
            'error': 'Max retry attempts reached',
            'attempts': retry_count
        })
        return None
    
    def process_all_credentials(self, max_concurrent=5):
        """Process all credentials with concurrency control"""
        credentials = self.load_credentials()
        
        if not credentials:
            logger.error("No credentials loaded")
            return
            
        logger.info(f"Starting to process {len(credentials)} credentials")
        
        # Process in batches to avoid overwhelming the server
        batch_size = max_concurrent
        total_processed = 0
        
        for i in range(0, len(credentials), batch_size):
            batch = credentials[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: credentials {i+1}-{min(i+batch_size, len(credentials))}")
            
            for credential in batch:
                result = self.process_single_credential(credential)
                total_processed += 1
                
                # Add delay between requests to avoid rate limiting
                time.sleep(0.5)
                
                if total_processed % 10 == 0:
                    logger.info(f"Progress: {total_processed}/{len(credentials)} processed")
            
            # Longer delay between batches
            if i + batch_size < len(credentials):
                logger.info("Waiting 2 seconds before next batch...")
                time.sleep(2)
        
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
        except Exception as e:
            logger.error(f"Error testing like feature: {e}")

def main():
    processor = IndCredentialsProcessor()
    
    # Process all credentials
    processor.process_all_credentials()
    
    # Test like feature if we have successful tokens
    if processor.successful_tokens:
        logger.info("Testing like feature...")
        asyncio.run(processor.test_like_feature())

if __name__ == "__main__":
    main()