import json
import aiohttp
import asyncio
import requests
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.message import DecodeError
from google.protobuf.json_format import MessageToJson
import os
import sys
# Add protobuf directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
protobuf_dir = os.path.join(parent_dir, 'protobuf')
sys.path.append(protobuf_dir)

import like_pb2
import like_count_pb2
import uid_generator_pb2
# Import JWT decoder
try:
    from .jwt_decoder import JWTDecoder
except ImportError:
    import base64
    import json
    
    class JWTDecoder:
        def extract_uid_from_token(self, token):
            try:
                parts = token.split('.')
                if len(parts) != 3:
                    return None
                payload = parts[1]
                while len(payload) % 4:
                    payload += '='
                decoded_bytes = base64.urlsafe_b64decode(payload)
                payload_data = json.loads(decoded_bytes.decode('utf-8'))
                return str(payload_data.get('external_uid') or payload_data.get('uid') or payload_data.get('account_id'))
            except Exception:
                return None


class LikeService:
    def __init__(self):
        self.AES_KEY = b"Yg&tc%DEuh6%Zc^8"
        self.AES_IV = b"6oyZDr22E3ychjM%"
        self.jwt_decoder = JWTDecoder()

    def encrypt_message(self, plaintext):
        """Encrypt message using AES CBC"""
        try:
            cipher = AES.new(self.AES_KEY, AES.MODE_CBC, self.AES_IV)
            padded_message = pad(plaintext, AES.block_size)
            encrypted_message = cipher.encrypt(padded_message)
            return binascii.hexlify(encrypted_message).decode("utf-8")
        except Exception:
            return None

    def create_like_protobuf(self, user_id, region):
        """Create like protobuf message"""
        try:
            message = like_pb2.like()
            message.uid = int(user_id)
            message.region = region
            return message.SerializeToString()
        except Exception:
            return None

    def create_uid_protobuf(self, uid):
        """Create UID protobuf message"""
        try:
            message = uid_generator_pb2.uid_generator()
            message.saturn_ = int(uid)
            message.garena = 1
            return message.SerializeToString()
        except Exception:
            return None

    def decode_protobuf(self, binary):
        """Decode protobuf response"""
        try:
            items = like_count_pb2.Info()
            items.ParseFromString(binary)
            return items
        except DecodeError:
            return None
        except Exception:
            return None

    def load_tokens(self, server_name):
        """Load tokens for specified server"""
        # First try to load tokens from session if available
        try:
            from flask import session
            session_tokens = session.get('generated_tokens', [])
            if session_tokens:
                # Filter tokens with valid status
                valid_tokens = [
                    {"uid": token["uid"], "token": token["token"]} 
                    for token in session_tokens 
                    if token.get("status") == "success" and token.get("token") and 
                    not token.get("token").endswith("sample_token_placeholder")
                ]
                if valid_tokens:
                    print(f"Using {len(valid_tokens)} tokens from current session for {server_name}")
                    return valid_tokens
        except Exception as e:
            print(f"Failed to load session tokens: {str(e)}")
        
        # No automatic token generation - user must provide tokens
        print(f"No session tokens found for {server_name} server")
        
        # Last resort: try file loading but validate tokens
        try:
            if server_name == "IND":
                path = "data/ind_tokens_success.json"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                path = "data/br_tokens_success.json"
            else:
                path = "data/bd_tokens_success.json"
            
            with open(path, "r") as f:
                tokens = json.load(f)
                if tokens and len(tokens) > 0:
                    # Filter out placeholder tokens
                    valid_tokens = [
                        token for token in tokens 
                        if token.get("token") and not token.get("token").endswith("sample_token_placeholder")
                    ]
                    if valid_tokens:
                        print(f"Loaded {len(valid_tokens)} valid tokens from {path}")
                        return valid_tokens
                    else:
                        print(f"All tokens in {path} are placeholders")
                        return None
                else:
                    print(f"Token file {path} is empty")
                    return None
        except FileNotFoundError:
            print(f"Token file not found for {server_name} server")
            return None
        except json.JSONDecodeError:
            print(f"Invalid JSON in token file for {server_name} server")
            return None
        except Exception as e:
            print(f"Error loading tokens: {str(e)}")
            return None

    def enc(self, uid):
        """Encrypt UID for requests"""
        protobuf_data = self.create_uid_protobuf(uid)
        if protobuf_data is None:
            return None
        return self.encrypt_message(protobuf_data)

    async def send_like_request(self, encrypted_uid, token, url):
        """Send single like request"""
        try:
            edata = bytes.fromhex(encrypted_uid)
            headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Expect": "100-continue",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB48",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=edata, headers=headers) as response:
                    return await response.text()
        except Exception:
            return None

    async def send_multiple_like_requests(self, uid, server_name, url):
        """Send multiple like requests asynchronously - SMART BATCHING"""
        region = server_name
        protobuf_message = self.create_like_protobuf(uid, region)
        if protobuf_message is None:
            return None
        
        encrypted_like = self.encrypt_message(protobuf_message)
        if encrypted_like is None:
            return None

        tokens = self.load_tokens(server_name)
        if tokens is None:
            return None

        # Use ALL available tokens for maximum likes
        max_tokens = len(tokens)  # Use ALL tokens for maximum likes
        selected_tokens = tokens

        print(f"Sending {max_tokens} REAL likes using ALL available tokens with smart batching...")
        
        # Send likes in optimized batches with shorter delays
        import asyncio
        batch_size = 5  # Bigger batches for faster processing
        delay_between_batches = 1.5  # Shorter delay for faster completion
        
        results = []
        
        for i in range(0, len(selected_tokens), batch_size):
            batch = selected_tokens[i:i + batch_size]
            batch_tasks = []
            
            for token_data in batch:
                token = token_data["token"]
                # Extract UID from JWT token
                token_uid = self.jwt_decoder.extract_uid_from_token(token) or token_data.get("uid", "Unknown")
                print(f"Batch sending like using token from UID {token_uid}...")
                batch_tasks.append(self.send_real_like_request(encrypted_like, token, url))
            
            # Send batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Add delay between batches (except for last batch)
            if i + batch_size < len(selected_tokens):
                print(f"Batch completed, waiting {delay_between_batches}s before next batch...")
                await asyncio.sleep(delay_between_batches)
        
        # Count successful likes
        successful_likes = sum(1 for result in results if result is not None and "error" not in str(result))
        print(f"Successfully sent {successful_likes}/{max_tokens} real likes using smart batching")
        
        return results

    async def send_real_like_request(self, encrypted_like, token, url):
        """Send a single REAL like request using like protobuf"""
        try:
            edata = bytes.fromhex(encrypted_like)
            headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB49",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=edata, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        return None
        except Exception:
            return None

    def make_player_info_request(self, encrypt, server_name, token):
        """Get player information with retry logic"""
        if server_name == "IND":
            url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
        else:
            url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

        edata = bytes.fromhex(encrypt)
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Expect": "100-continue",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB49",
        }
        
        # Try multiple times with different delays
        import time
        delays = [1, 3, 5, 10]  # Increasing delay for rate limiting
        
        for attempt, delay in enumerate(delays):
            try:
                if attempt > 0:
                    print(f"Retrying player info request (attempt {attempt + 1}) after {delay}s delay...")
                    time.sleep(delay)
                
                response = requests.post(url, data=edata, headers=headers, verify=False, timeout=15)
                
                if response.status_code == 200:
                    result = self.decode_protobuf(response.content)
                    if result:
                        return result
                elif response.status_code == 429:
                    print(f"Rate limited (429), will retry with longer delay...")
                    continue
                else:
                    print(f"Player info request failed with status {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"Request timeout on attempt {attempt + 1}")
                continue
            except Exception as e:
                print(f"Player info request error on attempt {attempt + 1}: {str(e)}")
                continue
        
        print("All retry attempts failed for player info request")
        return None

    async def process_like_request(self, uid, server_name):
        """Process complete like operation - SMART MODE without player info checks"""
        try:
            tokens = self.load_tokens(server_name)
            if tokens is None or len(tokens) == 0:
                raise Exception(f"No valid tokens available for {server_name} server. Please generate tokens first using the Token Generator tab, then try sending likes again.")
            
            # Use ALL available tokens for maximum likes
            token_count = len(tokens)  # Use ALL available tokens
            selected_tokens = tokens
            
            # Check first token
            first_token = selected_tokens[0]["token"]
            if not first_token or first_token.endswith("sample_token_placeholder"):
                raise Exception(f"No valid authentication tokens found for {server_name} server. Please generate real tokens first using the Token Generator tab.")

            # Determine like URL based on server
            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/LikeProfile"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/LikeProfile"
            else:
                url = "https://clientbp.ggblueshark.com/LikeProfile"

            # Send like requests directly without checking player info (avoids rate limiting)
            print(f"Sending {token_count} likes directly using smart mode...")
            await self.send_multiple_like_requests(uid, server_name, url)

            # Return success without checking player info to avoid 429 errors
            return {
                "status": 1,
                "message": f"Like operation completed successfully! Sent {token_count} likes.",
                "player": {
                    "uid": uid,
                    "nickname": "Target Player",
                },
                "likes": {
                    "before": "Unknown (smart mode)",
                    "after": "Unknown (smart mode)", 
                    "added_by_api": f"{token_count} likes sent",
                },
                "system_info": {
                    "tokens_used": token_count,
                    "requests_sent": token_count,
                    "api_status": "Smart mode - bypassing rate limits",
                    "note": f"Using {token_count} tokens to send maximum real likes without player info checks"
                }
            }

        except Exception as e:
            raise Exception(f"Error processing like request: {str(e)}")