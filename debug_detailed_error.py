#!/usr/bin/env python3
"""
Debug detailed error for player info request
"""
import json
import requests
from utils.like_service import LikeService
from google.protobuf.json_format import MessageToJson

def debug_player_info_request():
    """Debug the player info request in detail"""
    target_uid = "2926998273"
    server_name = "IND"
    
    print(f"Debugging player info request for UID: {target_uid}")
    print(f"Server: {server_name}")
    print("-" * 50)
    
    try:
        # Initialize like service
        like_service = LikeService()
        
        # Get tokens
        tokens = like_service.load_tokens(server_name)
        if not tokens:
            print("❌ No tokens available")
            return
        
        token = tokens[0]["token"]
        print(f"✓ Token loaded")
        
        # Encrypt UID
        encrypted_uid = like_service.enc(target_uid)
        if not encrypted_uid:
            print("❌ Failed to encrypt UID")
            return
        
        print(f"✓ UID encrypted: {encrypted_uid[:50]}...")
        
        # Manual request to debug
        url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        
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
        
        print(f"✓ Making request to: {url}")
        print(f"✓ Data length: {len(edata)} bytes")
        
        try:
            response = requests.post(url, data=edata, headers=headers, verify=False, timeout=10)
            print(f"✓ Response status: {response.status_code}")
            print(f"✓ Response length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                print("✓ Request successful!")
                
                # Try to decode protobuf
                try:
                    result = like_service.decode_protobuf(response.content)
                    if result:
                        print("✓ Protobuf decoded successfully!")
                        
                        # Convert to JSON
                        data = json.loads(MessageToJson(result))
                        print("\n--- Player Information ---")
                        account_info = data.get("AccountInfo", {})
                        
                        print(f"UID: {account_info.get('UID', 'Unknown')}")
                        print(f"Player Name: {account_info.get('PlayerNickname', 'Unknown')}")
                        print(f"Current Likes: {account_info.get('Likes', 0)}")
                        print(f"Level: {account_info.get('Level', 'Unknown')}")
                        
                        return True
                    else:
                        print("❌ Failed to decode protobuf")
                        print(f"Raw response: {response.content[:200]}...")
                        
                except Exception as decode_e:
                    print(f"❌ Decode error: {str(decode_e)}")
                    print(f"Raw response: {response.content[:200]}...")
                    
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout")
        except Exception as req_e:
            print(f"❌ Request error: {str(req_e)}")
            
    except Exception as e:
        print(f"❌ General error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    return False

if __name__ == "__main__":
    debug_player_info_request()