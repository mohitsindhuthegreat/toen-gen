#!/usr/bin/env python3
"""
Test different servers and approaches for ID 2926998273
"""
import time
import requests
from utils.like_service import LikeService

def test_different_approaches():
    """Test different servers and approaches"""
    target_uid = "2926998273"
    
    print(f"Testing different approaches for UID: {target_uid}")
    print("-" * 50)
    
    like_service = LikeService()
    
    # Test different servers
    servers = ["IND", "US", "BR"]
    
    for server in servers:
        print(f"\n--- Testing {server} server ---")
        
        try:
            # Get tokens for this server
            tokens = like_service.load_tokens(server)
            if not tokens:
                print(f"❌ No tokens available for {server}")
                continue
            
            token = tokens[0]["token"]
            encrypted_uid = like_service.enc(target_uid)
            
            if not encrypted_uid:
                print(f"❌ Failed to encrypt UID for {server}")
                continue
            
            # Determine URL based on server
            if server == "IND":
                url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
            elif server in ["US", "BR"]:
                url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
            else:
                url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
            
            print(f"Testing URL: {url}")
            
            # Make request
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
            
            response = requests.post(url, data=edata, headers=headers, verify=False, timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✓ {server} server is working!")
                
                # Try to decode
                result = like_service.decode_protobuf(response.content)
                if result:
                    print(f"✓ Player info decoded successfully on {server}")
                    
                    # Try to send like directly
                    print(f"Now trying to send like on {server}...")
                    
                    like_url = url.replace("GetPlayerPersonalShow", "LikeProfile")
                    like_response = requests.post(like_url, data=edata, headers=headers, verify=False, timeout=10)
                    
                    print(f"Like response status: {like_response.status_code}")
                    
                    if like_response.status_code == 200:
                        print(f"✓ Like sent successfully on {server}!")
                        return True
                    else:
                        print(f"❌ Like failed on {server}")
                        
                else:
                    print(f"❌ Failed to decode response on {server}")
                    
            elif response.status_code == 503:
                print(f"❌ {server} server temporarily unavailable")
            elif response.status_code == 401:
                print(f"❌ {server} server rejected token")
            else:
                print(f"❌ {server} server returned {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error with {server}: {str(e)}")
            
        # Small delay between servers
        time.sleep(1)
        
    return False

if __name__ == "__main__":
    test_different_approaches()