#!/usr/bin/env python3
"""
Test token validity and actual like sending capability
"""
import json
import requests
from utils.like_service import LikeService
from google.protobuf.json_format import MessageToJson

def test_token_validity():
    """Test if tokens are actually valid and can send likes"""
    target_uid = "2926998273"
    server_name = "IND"
    
    print(f"Testing token validity for UID: {target_uid}")
    print("-" * 50)
    
    like_service = LikeService()
    
    # Load tokens
    tokens = like_service.load_tokens(server_name)
    if not tokens:
        print("❌ No tokens available")
        return False
    
    print(f"✓ Found {len(tokens)} tokens")
    
    # Test each token
    for i, token_data in enumerate(tokens):
        print(f"\n--- Testing Token {i+1} ---")
        token = token_data["token"]
        token_uid = token_data.get("uid", "Unknown")
        
        print(f"Token UID: {token_uid}")
        print(f"Token: {token[:50]}...")
        
        # Test token with validation endpoints
        validation_endpoints = [
            "https://client.ind.freefiremobile.com/LikeProfile",
            "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        ]
        
        for endpoint in validation_endpoints:
            try:
                # Create test payload
                encrypted_uid = like_service.enc(target_uid)
                if not encrypted_uid:
                    print(f"❌ Failed to encrypt UID")
                    continue
                
                edata = bytes.fromhex(encrypted_uid)
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
                
                response = requests.post(endpoint, data=edata, headers=headers, verify=False, timeout=10)
                
                print(f"Endpoint: {endpoint.split('/')[-1]}")
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✓ Token is valid!")
                    
                    # If this is the like endpoint, check if like was actually sent
                    if "LikeProfile" in endpoint:
                        print("✓ Like request successful!")
                        
                        # Get player info to check if likes increased
                        player_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
                        if player_info:
                            data = json.loads(MessageToJson(player_info))
                            current_likes = data.get("AccountInfo", {}).get("Likes", 0)
                            print(f"Current likes: {current_likes}")
                        
                elif response.status_code == 401:
                    print("❌ Token expired or invalid")
                elif response.status_code == 403:
                    print("⚠️ Token valid but action forbidden")
                elif response.status_code == 503:
                    print("⚠️ Server temporarily unavailable")
                else:
                    print(f"❌ Unexpected status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error testing endpoint: {str(e)}")
        
        # Test with multiple rapid requests to simulate bulk like sending
        print("\n--- Testing Bulk Like Sending ---")
        successful_likes = 0
        
        for j in range(5):  # Send 5 likes quickly
            try:
                encrypted_uid = like_service.enc(target_uid)
                edata = bytes.fromhex(encrypted_uid)
                
                response = requests.post(
                    "https://client.ind.freefiremobile.com/LikeProfile",
                    data=edata,
                    headers=headers,
                    verify=False,
                    timeout=5
                )
                
                if response.status_code == 200:
                    successful_likes += 1
                    print(f"✓ Like {j+1} sent successfully")
                else:
                    print(f"❌ Like {j+1} failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Like {j+1} error: {str(e)}")
        
        print(f"\nBulk result: {successful_likes}/5 likes sent successfully")
        
        if successful_likes > 0:
            return True
    
    return False

if __name__ == "__main__":
    test_token_validity()