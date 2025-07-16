#!/usr/bin/env python3
"""
Generate maximum tokens from all available credentials
"""
import json
import logging
import asyncio
from utils.proper_token_generator import ProperTokenGenerator

class MaxTokenGenerator:
    def __init__(self):
        self.successful_tokens = []
        self.failed_tokens = []
        self.generator = ProperTokenGenerator()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def load_credentials(self, file_path='ind.json'):
        """Load credentials from JSON file"""
        try:
            with open(file_path, 'r') as f:
                credentials = json.load(f)
            self.logger.info(f"Loaded {len(credentials)} credentials from {file_path}")
            return credentials
        except Exception as e:
            self.logger.error(f"Error loading credentials: {e}")
            return []

    def extract_uid_password(self, credential_data):
        """Extract UID and password from credential data"""
        try:
            import base64
            if 'data' in credential_data:
                decoded = base64.b64decode(credential_data['data']).decode('utf-8')
                data = json.loads(decoded)
                uid = data.get('uid')
                password = data.get('password')
                return uid, password
        except Exception as e:
            self.logger.error(f"Error extracting credentials: {e}")
        return None, None

    def process_credentials_batch(self, credentials, max_tokens=50):
        """Process credentials in batch to generate tokens"""
        self.logger.info(f"Processing {min(len(credentials), max_tokens)} credentials")
        
        for i, cred in enumerate(credentials[:max_tokens]):
            uid, password = self.extract_uid_password(cred)
            
            if uid and password:
                self.logger.info(f"Processing credential {i+1}/{min(len(credentials), max_tokens)}: UID {uid}")
                
                try:
                    result = self.generator.generate_token(uid, password)
                    if result and result.get('success'):
                        token_data = {
                            "uid": uid,
                            "token": result['token'],
                            "server": "IND"
                        }
                        self.successful_tokens.append(token_data)
                        self.logger.info(f"✓ Successfully generated token for UID: {uid}")
                    else:
                        self.logger.error(f"❌ Failed to generate token for UID: {uid}")
                        self.failed_tokens.append(uid)
                        
                except Exception as e:
                    self.logger.error(f"❌ Error processing UID {uid}: {e}")
                    self.failed_tokens.append(uid)
                    
            else:
                self.logger.warning(f"❌ Could not extract UID/password from credential {i+1}")

    def save_tokens(self, filename='max_tokens_success.json'):
        """Save successful tokens to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.successful_tokens, f, indent=2)
            self.logger.info(f"Saved {len(self.successful_tokens)} tokens to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving tokens: {e}")

    def print_summary(self):
        """Print processing summary"""
        print(f"\n--- TOKEN GENERATION SUMMARY ---")
        print(f"✓ Successful tokens: {len(self.successful_tokens)}")
        print(f"❌ Failed tokens: {len(self.failed_tokens)}")
        print(f"📊 Success rate: {len(self.successful_tokens)/(len(self.successful_tokens)+len(self.failed_tokens))*100:.1f}%")
        
        if self.successful_tokens:
            print(f"\n🎯 Maximum possible likes: {len(self.successful_tokens)} (one per token)")

def main():
    generator = MaxTokenGenerator()
    
    # Load credentials
    credentials = generator.load_credentials()
    if not credentials:
        print("No credentials found!")
        return
    
    # Process first 30 credentials (to avoid timeout)
    generator.process_credentials_batch(credentials, max_tokens=30)
    
    # Save results
    generator.save_tokens()
    generator.print_summary()

if __name__ == "__main__":
    main()