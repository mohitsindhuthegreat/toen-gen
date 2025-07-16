#!/usr/bin/env python3
"""
Generate ALL possible tokens from credentials file
"""
import json
import asyncio
from utils.token_generator import TokenGenerator
from flask_caching import Cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AllTokensGenerator:
    def __init__(self):
        self.cache = Cache(config={'CACHE_TYPE': 'simple'})
        self.token_generator = TokenGenerator(cache=self.cache)
        self.successful_tokens = []
        self.failed_count = 0
        
    def load_credentials(self):
        """Load all credentials"""
        try:
            with open('ind.json', 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} credentials")
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
            return uid, password
        except:
            return None, None
    
    def process_credential(self, credential_data):
        """Process a single credential quickly"""
        uid, password = self.extract_uid_password(credential_data)
        
        if not uid or not password:
            return None
            
        try:
            # Generate token with shorter timeout
            result = self.token_generator.generate_token(uid, password)
            
            if result and result.get('status') == 'success':
                token_data = {
                    'uid': uid,
                    'token': result.get('token'),
                    'server': 'IND'
                }
                self.successful_tokens.append(token_data)
                logger.info(f"✓ Token {len(self.successful_tokens)}: UID {uid}")
                return token_data
            else:
                self.failed_count += 1
                return None
                
        except Exception as e:
            self.failed_count += 1
            return None
    
    def process_all_credentials(self):
        """Process all credentials efficiently"""
        credentials = self.load_credentials()
        
        logger.info(f"Processing ALL {len(credentials)} credentials...")
        
        for i, cred in enumerate(credentials):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(credentials)} processed, {len(self.successful_tokens)} successful")
            
            self.process_credential(cred)
            
            # Stop if we have enough tokens or hit too many failures
            if len(self.successful_tokens) >= 100 or self.failed_count > 50:
                break
        
        return self.successful_tokens
    
    def save_tokens(self):
        """Save all tokens"""
        try:
            with open('ind_tokens_success.json', 'w') as f:
                json.dump(self.successful_tokens, f, indent=2)
            logger.info(f"Saved {len(self.successful_tokens)} tokens")
        except Exception as e:
            logger.error(f"Error saving tokens: {e}")

def main():
    generator = AllTokensGenerator()
    
    # Process all credentials
    tokens = generator.process_all_credentials()
    
    # Save results
    generator.save_tokens()
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"✓ Total working tokens: {len(tokens)}")
    print(f"❌ Failed credentials: {generator.failed_count}")
    print(f"🚀 Maximum real likes per request: {len(tokens)}")
    
    return tokens

if __name__ == "__main__":
    main()