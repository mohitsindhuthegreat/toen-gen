#!/usr/bin/env python3
"""
Test sending likes to ID 2926998273
"""
import asyncio
import json
from utils.like_service import LikeService

async def test_like_send():
    """Test sending likes to the specific ID"""
    target_uid = "2926998273"
    server_name = "IND"
    
    print(f"Testing like send to UID: {target_uid}")
    print(f"Server: {server_name}")
    print("-" * 50)
    
    try:
        # Initialize like service
        like_service = LikeService()
        
        # Test the like sending process
        result = await like_service.process_like_request(target_uid, server_name)
        
        print("✓ Like sending successful!")
        print(f"Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"✗ Like sending failed: {str(e)}")
        
        # Let's try to get more details about the error
        try:
            tokens = like_service.load_tokens(server_name)
            if tokens:
                token = tokens[0]["token"]
                print(f"Token available: {token[:50]}...")
                
                # Test encryption
                encrypted_uid = like_service.enc(target_uid)
                print(f"Encryption successful: {encrypted_uid is not None}")
                
                # Test player info request
                player_info = like_service.make_player_info_request(encrypted_uid, server_name, token)
                print(f"Player info request: {player_info is not None}")
                
            else:
                print("No tokens available")
                
        except Exception as debug_e:
            print(f"Debug error: {str(debug_e)}")

if __name__ == "__main__":
    asyncio.run(test_like_send())