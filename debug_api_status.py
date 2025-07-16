#!/usr/bin/env python3
"""
Debug API status and test different endpoints
"""
import requests
import json
from utils.like_service import LikeService

def test_api_endpoints():
    """Test different API endpoints to check server status"""
    
    # Load tokens
    like_service = LikeService()
    tokens = like_service.load_tokens("IND")
    
    if not tokens:
        print("❌ No tokens available")
        return
    
    token = tokens[0]["token"]
    print(f"✓ Token loaded: {token[:50]}...")
    
    # Test different endpoints
    endpoints = [
        ("IND Player Info", "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"),
        ("IND Like Profile", "https://client.ind.freefiremobile.com/LikeProfile"),
        ("US Player Info", "https://client.us.freefiremobile.com/GetPlayerPersonalShow"),
        ("US Like Profile", "https://client.us.freefiremobile.com/LikeProfile"),
    ]
    
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
    
    # Test with a dummy UID first to see general server status
    test_uid = "2926998273"
    encrypted_uid = like_service.enc(test_uid)
    
    if not encrypted_uid:
        print("❌ Failed to encrypt UID")
        return
    
    print(f"✓ Encrypted UID: {encrypted_uid[:50]}...")
    
    for name, url in endpoints:
        print(f"\n--- Testing {name} ---")
        try:
            edata = bytes.fromhex(encrypted_uid)
            response = requests.post(url, data=edata, headers=headers, verify=False, timeout=5)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                print("✓ API is working!")
                # Try to decode response
                try:
                    result = like_service.decode_protobuf(response.content)
                    if result:
                        print("✓ Response decoded successfully")
                    else:
                        print("❌ Failed to decode response")
                except Exception as e:
                    print(f"❌ Decode error: {str(e)}")
            elif response.status_code == 503:
                print("❌ Service unavailable (503)")
            elif response.status_code == 401:
                print("❌ Unauthorized (401) - Token may be expired")
            elif response.status_code == 404:
                print("❌ Not found (404)")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout")
        except Exception as e:
            print(f"❌ Request error: {str(e)}")

if __name__ == "__main__":
    test_api_endpoints()