#!/usr/bin/env python3
"""
Test the like feature with generated tokens
"""

import asyncio
import json
from utils.like_service import LikeService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_like_feature():
    """Test the like feature"""
    like_service = LikeService()
    target_uid = "6780791579"
    
    logger.info(f"Testing like feature for target UID: {target_uid}")
    
    # Check if tokens exist
    try:
        with open('tokens/ind.json', 'r') as f:
            tokens = json.load(f)
        logger.info(f"Found {len(tokens)} tokens for IND server")
        
        # Display some token info
        for i, token in enumerate(tokens[:3]):
            logger.info(f"Token {i+1}: UID {token['uid']} - {token['token'][:50]}...")
    except Exception as e:
        logger.error(f"Error loading tokens: {e}")
        return
    
    try:
        # Test the like feature
        result = await like_service.process_like_request(target_uid, 'IND')
        logger.info(f"Like feature result: {result}")
        
        if result:
            logger.info("✓ Like feature is working!")
            return True
        else:
            logger.warning("Like feature returned no result")
            return False
            
    except Exception as e:
        logger.error(f"Error testing like feature: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_like_feature())
    if result:
        print("SUCCESS: Like feature is working with generated tokens!")
    else:
        print("FAILED: Like feature needs troubleshooting")