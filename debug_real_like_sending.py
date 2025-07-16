#!/usr/bin/env python3
"""
Debug real like sending - check if we're actually sending real likes
"""
import requests
import json
from utils.like_service import LikeService
from google.protobuf.json_format import MessageToJson

def debug_real_like_sending():
    """Debug the actual like sending process"""
    target_uid = "2160677649"  # Test player
    server_name = "IND"
    
    print(f"Debugging Real Like Sending for UID: {target_uid}")
    print("-" * 50)
    
    like_service = LikeService()
    
    # Load tokens
    tokens = like_service.load_tokens(server_name)
    if not tokens:
        print("❌ No tokens available")
        return
    
    token = tokens[0]["token"]
    print(f"✓ Token loaded: {token[:50]}...")
    
    # Get initial player info
    encrypted_uid = like_service.enc(target_uid)
    initial_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
    
    if initial_info:
        data = json.loads(MessageToJson(initial_info))
        initial_likes = int(data.get("AccountInfo", {}).get("Likes", 0))
        player_name = data.get("AccountInfo", {}).get("PlayerNickname", "Unknown")
        print(f"✓ Player: {player_name}")
        print(f"✓ Initial likes: {initial_likes}")
    else:
        print("❌ Failed to get initial player info")
        return
    
    # Test the ACTUAL like sending mechanism
    print("\n--- Testing Real Like Sending ---")
    
    # Method 1: Using like protobuf (current method)
    print("\n1. Testing with Like Protobuf:")
    like_protobuf = like_service.create_like_protobuf(target_uid, server_name)
    if like_protobuf:
        encrypted_like = like_service.encrypt_message(like_protobuf)
        if encrypted_like:
            print(f"✓ Like protobuf created and encrypted")
            
            # Send the encrypted like
            like_url = "https://client.ind.freefiremobile.com/LikeProfile"
            
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
                
                response = requests.post(like_url, data=edata, headers=headers, verify=False, timeout=10)
                print(f"Like response status: {response.status_code}")
                print(f"Response content: {response.content}")
                
                # Check if likes actually increased
                import time
                time.sleep(2)
                
                updated_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
                if updated_info:
                    data = json.loads(MessageToJson(updated_info))
                    final_likes = int(data.get("AccountInfo", {}).get("Likes", 0))
                    likes_added = final_likes - initial_likes
                    
                    print(f"Final likes: {final_likes}")
                    print(f"Real likes added: {likes_added}")
                    
                    if likes_added > 0:
                        print("✓ REAL LIKES WERE ADDED!")
                        return True
                    else:
                        print("❌ No real likes added")
                        
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    # Method 2: Try different approach - SendLikes endpoint
    print("\n2. Testing with SendLikes endpoint:")
    try:
        send_likes_url = "https://client.ind.freefiremobile.com/SendLikes"
        
        # Create like protobuf for SendLikes
        like_protobuf = like_service.create_like_protobuf(target_uid, server_name)
        if like_protobuf:
            encrypted_like = like_service.encrypt_message(like_protobuf)
            edata = bytes.fromhex(encrypted_like)
            
            response = requests.post(send_likes_url, data=edata, headers=headers, verify=False, timeout=10)
            print(f"SendLikes response status: {response.status_code}")
            print(f"Response content: {response.content}")
            
            # Check if likes increased
            time.sleep(2)
            updated_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
            if updated_info:
                data = json.loads(MessageToJson(updated_info))
                final_likes = int(data.get("AccountInfo", {}).get("Likes", 0))
                likes_added = final_likes - initial_likes
                
                print(f"Final likes after SendLikes: {final_likes}")
                print(f"Real likes added: {likes_added}")
                
                if likes_added > 0:
                    print("✓ REAL LIKES WERE ADDED WITH SENDLIKES!")
                    return True
                    
    except Exception as e:
        print(f"❌ SendLikes error: {str(e)}")
    
    print("\n--- Summary ---")
    print("Testing different methods to send real likes...")
    
    return False

if __name__ == "__main__":
    debug_real_like_sending()