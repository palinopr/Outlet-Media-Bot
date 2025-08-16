#!/usr/bin/env python3
"""
Test the agent's response directly to see what it returns
"""
import os
import asyncio
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent

# Load environment variables
load_dotenv()

async def test_agent():
    # Initialize agent
    agent = MetaAdsAgent()
    
    # Test the same query
    query = "How Ryan campings cities tell me sales spend and roas"
    
    print("Query:", query)
    print("=" * 60)
    
    # Get response
    response = await agent.process_request(query)
    
    print("Agent Response:")
    print(response)
    
    return response

if __name__ == '__main__':
    asyncio.run(test_agent())