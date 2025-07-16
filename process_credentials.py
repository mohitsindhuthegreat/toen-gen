import json
import requests
import time
from utils.token_generator import TokenGenerator

def process_credentials_file():
    """Process credentials file and generate tokens for all accounts"""
    try:
        # Load credentials
        with open('attached_assets/credentials_1752645952395.json', 'r') as f:
            credentials = json.load(f)
        
        print(f"Found {len(credentials)} credentials to process")
        
        # Initialize token generator
        generator = TokenGenerator()
        tokens = []
        
        for i, cred in enumerate(credentials):
            try:
                guest_info = cred.get('guest_account_info', {})
                uid = guest_info.get('com.garena.msdk.guest_uid')
                password = guest_info.get('com.garena.msdk.guest_password')
                
                if uid and password:
                    print(f"Processing {i+1}/{len(credentials)}: UID {uid}")
                    
                    result = generator.generate_token(uid, password)
                    if result and result.get('status') == 'success':
                        token_data = {
                            "token": result.get('token'),
                            "uid": uid,
                            "generated_at": result.get('generated_at')
                        }
                        tokens.append(token_data)
                        print(f"✅ Token generated for UID {uid}")
                    else:
                        print(f"❌ Failed to generate token for UID {uid}")
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing credential {i+1}: {str(e)}")
                continue
        
        # Save tokens to ind.json
        with open('tokens/ind.json', 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print(f"✅ Successfully generated {len(tokens)} tokens and saved to tokens/ind.json")
        return True
        
    except Exception as e:
        print(f"Error processing credentials: {str(e)}")
        return False

if __name__ == "__main__":
    process_credentials_file()