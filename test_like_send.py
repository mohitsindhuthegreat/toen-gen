#!/usr/bin/env python3
"""
Test sending likes to specified UID
"""

import json
import asyncio
import requests
from utils.like_service import LikeService
from utils.token_generator import TokenGenerator
from flask_caching import Cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LikeTester:
    def __init__(self):
        self.like_service = LikeService()
        self.cache = Cache(config={'CACHE_TYPE': 'simple'})
        self.token_generator = TokenGenerator(cache=self.cache)
        
    def get_player_info(self, uid, token):
        """Get player information before sending likes"""
        try:
            encrypted_uid = self.like_service.enc(uid)
            if not encrypted_uid:
                return None
                
            url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
            
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
            
            edata = bytes.fromhex(encrypted_uid)
            response = requests.post(url, data=edata, headers=headers, verify=False, timeout=10)
            
            if response.status_code == 200:
                result = self.like_service.decode_protobuf(response.content)
                if result:
                    return result
                else:
                    logger.warning(f"Failed to decode protobuf for UID {uid}")
                    return None
            else:
                logger.warning(f"HTTP error {response.status_code} for UID {uid}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting player info for UID {uid}: {e}")
            return None
    
    async def send_single_like(self, target_uid, token):
        """Send a single like to target UID"""
        try:
            # Create like protobuf
            like_protobuf = self.like_service.create_like_protobuf(target_uid, "IND")
            if not like_protobuf:
                return None
                
            # Encrypt the message
            encrypted_like = self.like_service.encrypt_message(like_protobuf)
            if not encrypted_like:
                return None
            
            # Send like request
            url = "https://client.ind.freefiremobile.com/SendLikes"
            
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
            
            edata = bytes.fromhex(encrypted_like)
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=edata, headers=headers, ssl=False, timeout=10) as response:
                    if response.status == 200:
                        content = await response.read()
                        result = self.like_service.decode_protobuf(content)
                        return result
                    else:
                        logger.warning(f"Like send failed with status {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error sending like: {e}")
            return None
    
    async def test_like_sending(self, target_uid="6780791579"):
        """Test sending likes to target UID"""
        logger.info(f"Testing like sending to UID: {target_uid}")
        
        # Load tokens
        try:
            with open('tokens/ind.json', 'r') as f:
                tokens = json.load(f)
            logger.info(f"Loaded {len(tokens)} tokens")
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")
            return False
        
        if not tokens:
            logger.error("No tokens available")
            return False
        
        # Use first token for testing
        test_token = tokens[0]['token']
        logger.info(f"Using token from UID: {tokens[0]['uid']}")
        
        # Get initial player info
        logger.info("Getting initial player info...")
        initial_info = self.get_player_info(target_uid, test_token)
        
        if initial_info:
            logger.info("✓ Successfully retrieved player info")
            try:
                from google.protobuf.json_format import MessageToJson
                import json as json_lib
                data = json_lib.loads(MessageToJson(initial_info))
                initial_likes = data.get("AccountInfo", {}).get("Likes", "0")
                logger.info(f"Initial likes: {initial_likes}")
            except Exception as e:
                logger.info(f"Could not parse initial likes: {e}")
        else:
            logger.warning("Could not get initial player info")
        
        # Send multiple likes
        logger.info("Sending likes...")
        successful_likes = 0
        
        for i in range(min(5, len(tokens))):  # Send 5 likes using different tokens
            token = tokens[i]['token']
            logger.info(f"Sending like {i+1} using token from UID {tokens[i]['uid']}")
            
            result = await self.send_single_like(target_uid, token)
            
            if result:
                successful_likes += 1
                logger.info(f"✓ Like {i+1} sent successfully")
            else:
                logger.warning(f"✗ Like {i+1} failed")
            
            # Small delay between likes
            await asyncio.sleep(0.5)
        
        # Get final player info
        logger.info("Getting final player info...")
        final_info = self.get_player_info(target_uid, test_token)
        
        if final_info:
            try:
                from google.protobuf.json_format import MessageToJson
                import json as json_lib
                data = json_lib.loads(MessageToJson(final_info))
                final_likes = data.get("AccountInfo", {}).get("Likes", "0")
                logger.info(f"Final likes: {final_likes}")
            except Exception as e:
                logger.info(f"Could not parse final likes: {e}")
        
        logger.info(f"Successfully sent {successful_likes} likes")
        return successful_likes > 0

async def main():
    tester = LikeTester()
    result = await tester.test_like_sending("6780791579")
    
    if result:
        print("\n✓ SUCCESS: Likes are being sent successfully!")
    else:
        print("\n✗ FAILED: Like sending needs troubleshooting")

if __name__ == "__main__":
    asyncio.run(main())