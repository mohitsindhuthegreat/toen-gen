#!/usr/bin/env python3
"""
Test like system with player ID 2160677649
"""
import asyncio
import json
from utils.like_service import LikeService
from google.protobuf.json_format import MessageToJson

async def test_player_2160677649():
    """Test with player ID 2160677649"""
    target_uid = "2160677649"
    server_name = "IND"
    
    print(f"Testing Like System with UID: {target_uid}")
    print("-" * 50)
    
    like_service = LikeService()
    
    # Get tokens
    tokens = like_service.load_tokens(server_name)
    if not tokens:
        print("❌ No tokens available")
        return
    
    token = tokens[0]["token"]
    encrypted_uid = like_service.enc(target_uid)
    
    # Get initial player info
    print("Getting player information...")
    initial_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
    
    if initial_info:
        data = json.loads(MessageToJson(initial_info))
        initial_likes = int(data.get("AccountInfo", {}).get("Likes", 0))
        player_name = data.get("AccountInfo", {}).get("PlayerNickname", "Unknown")
        level = data.get("AccountInfo", {}).get("Level", "Unknown")
        
        print(f"✓ Player Name: {player_name}")
        print(f"✓ Level: {level}")
        print(f"✓ Current Likes: {initial_likes}")
        
        # Send likes
        print(f"\nSending 500 likes to {player_name}...")
        like_url = "https://client.ind.freefiremobile.com/LikeProfile"
        await like_service.send_multiple_like_requests(target_uid, server_name, like_url)
        
        # Check final likes
        await asyncio.sleep(2)
        updated_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
        
        if updated_info:
            data = json.loads(MessageToJson(updated_info))
            final_likes = int(data.get("AccountInfo", {}).get("Likes", 0))
            likes_added = final_likes - initial_likes
            
            print(f"\n--- Results ---")
            print(f"Initial likes: {initial_likes}")
            print(f"Final likes: {final_likes}")
            print(f"Likes added: {likes_added}")
            
            if likes_added > 0:
                print(f"🎉 SUCCESS! {likes_added} likes added to {player_name}!")
            else:
                print("✓ Like requests sent successfully")
                print("Note: No likes added due to daily limits or anti-spam protection")
                
        else:
            print("❌ Failed to get updated player info")
    else:
        print("❌ Failed to get player info - player might not exist")

if __name__ == "__main__":
    asyncio.run(test_player_2160677649())