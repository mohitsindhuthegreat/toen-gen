#!/usr/bin/env python3
"""
Test the improved real like sending system
"""
import asyncio
import json
from utils.like_service import LikeService
from google.protobuf.json_format import MessageToJson

async def test_real_like_system():
    """Test the real like sending system"""
    target_uid = "2160677649"
    server_name = "IND"
    
    print(f"Testing REAL Like System for UID: {target_uid}")
    print("-" * 50)
    
    like_service = LikeService()
    
    # Get tokens
    tokens = like_service.load_tokens(server_name)
    if not tokens:
        print("❌ No tokens available")
        return
    
    print(f"✓ Loaded {len(tokens)} tokens")
    
    token = tokens[0]["token"]
    encrypted_uid = like_service.enc(target_uid)
    
    # Get initial player info
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
    
    # Send real likes
    print("\nSending REAL likes...")
    like_url = "https://client.ind.freefiremobile.com/LikeProfile"
    await like_service.send_multiple_like_requests(target_uid, server_name, like_url)
    
    # Wait and check final likes
    await asyncio.sleep(3)
    
    final_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
    
    if final_info:
        data = json.loads(MessageToJson(final_info))
        final_likes = int(data.get("AccountInfo", {}).get("Likes", 0))
        real_likes_added = final_likes - initial_likes
        
        print(f"\n--- Results ---")
        print(f"Player: {player_name}")
        print(f"Initial likes: {initial_likes}")
        print(f"Final likes: {final_likes}")
        print(f"REAL likes added: {real_likes_added}")
        
        if real_likes_added > 0:
            print(f"🎉 SUCCESS! {real_likes_added} REAL likes were added!")
        else:
            print("Note: No likes added (may be due to daily limits)")
            
    else:
        print("❌ Failed to get final player info")

if __name__ == "__main__":
    asyncio.run(test_real_like_system())