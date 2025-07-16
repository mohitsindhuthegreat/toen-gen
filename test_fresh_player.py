#!/usr/bin/env python3
"""
Test with a fresh player to see if likes can be added
"""
import asyncio
import json
from utils.like_service import LikeService
from google.protobuf.json_format import MessageToJson

async def test_fresh_player():
    """Test with different players"""
    # Test with our own token UIDs (fresh players)
    test_players = [
        "3978250517",  # Our first token UID
        "3756802699",  # Our second token UID
        "1234567890",  # Random test ID
    ]
    
    server_name = "IND"
    like_service = LikeService()
    
    for target_uid in test_players:
        print(f"\n--- Testing with Player UID: {target_uid} ---")
        
        # Get tokens
        tokens = like_service.load_tokens(server_name)
        if not tokens:
            print("❌ No tokens available")
            continue
        
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
            
            # Send a few likes to test
            print(f"Sending REAL likes using ALL tokens...")
            like_url = "https://client.ind.freefiremobile.com/LikeProfile"
            
            # Send just 10 likes for testing
            region = server_name
            protobuf_message = like_service.create_like_protobuf(target_uid, region)
            encrypted_like = like_service.encrypt_message(protobuf_message)
            
            successful_likes = 0
            for i in range(10):
                token = tokens[i % len(tokens)]["token"]
                result = await like_service.send_real_like_request(encrypted_like, token, like_url)
                if result is not None:
                    successful_likes += 1
            
            print(f"✓ Sent {successful_likes}/10 like requests")
            
            # Check if likes increased
            await asyncio.sleep(2)
            updated_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
            
            if updated_info:
                data = json.loads(MessageToJson(updated_info))
                final_likes = int(data.get("AccountInfo", {}).get("Likes", 0))
                likes_added = final_likes - initial_likes
                
                print(f"✓ Final likes: {final_likes}")
                print(f"✓ Real likes added: {likes_added}")
                
                if likes_added > 0:
                    print(f"🎉 SUCCESS! {likes_added} real likes added to {player_name}!")
                    
                    # Now use the full system on this player
                    print(f"\nUsing FULL system on {player_name}...")
                    await like_service.send_multiple_like_requests(target_uid, server_name, like_url)
                    
                    await asyncio.sleep(3)
                    final_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
                    if final_info:
                        data = json.loads(MessageToJson(final_info))
                        final_final_likes = int(data.get("AccountInfo", {}).get("Likes", 0))
                        total_likes_added = final_final_likes - initial_likes
                        print(f"✓ TOTAL likes added with full system: {total_likes_added}")
                    
                    return True
                    
        else:
            print("❌ Player not found or invalid")
    
    return False

if __name__ == "__main__":
    asyncio.run(test_fresh_player())