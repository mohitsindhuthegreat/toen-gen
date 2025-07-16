#!/usr/bin/env python3
"""
Test player info for ID 2926998273
"""
import json
from utils.like_service import LikeService
from google.protobuf.json_format import MessageToJson

def test_player_info():
    """Test getting player info for the specific ID"""
    target_uid = "2926998273"
    server_name = "IND"
    
    print(f"Testing player info for UID: {target_uid}")
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
        
        print(f"✓ UID encrypted")
        
        # Get player info
        player_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
        
        if player_info:
            print("✓ Player info retrieved successfully!")
            
            # Convert to JSON for easy reading
            data = json.loads(MessageToJson(player_info))
            
            print("\n--- Player Information ---")
            account_info = data.get("AccountInfo", {})
            
            print(f"UID: {account_info.get('UID', 'Unknown')}")
            print(f"Player Name: {account_info.get('PlayerNickname', 'Unknown')}")
            print(f"Current Likes: {account_info.get('Likes', 0)}")
            print(f"Level: {account_info.get('Level', 'Unknown')}")
            print(f"Region: {account_info.get('Region', 'Unknown')}")
            
            print("\n--- Full JSON Response ---")
            print(json.dumps(data, indent=2))
            
        else:
            print("❌ Failed to get player info")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_player_info()