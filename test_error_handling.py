#!/usr/bin/env python3
"""Test agent error handling"""
import asyncio
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent
import json

load_dotenv()

async def test_error_handling():
    agent = MetaAdsAgent()
    
    print("TEST: Error Handling in Budget Update")
    print("=" * 70)
    
    # Simulate a request that will fail (typo in campaign name)
    request = "update budget for NONEXISTENT campaign brooklyn to $200"
    response = await agent.process_request(request)
    
    print("Agent Response:")
    print(response)
    print("\n" + "=" * 70)
    
    # Check if agent properly reported error
    if "unable" in response.lower() or "error" in response.lower() or "not found" in response.lower():
        print("✅ PASS: Agent properly reported the error")
    elif "successfully" in response.lower() or "updated" in response.lower():
        print("❌ FAIL: Agent claimed success despite error")
    else:
        print("⚠️ UNCLEAR: Response doesn't clearly indicate success or failure")
    
    print("\n" + "=" * 70)
    print("\nTEST 2: Valid request to check normal operation")
    request2 = "show me spend for Ryan Castro campaign"
    response2 = await agent.process_request(request2)
    print("Response to valid request:")
    print(response2)

if __name__ == "__main__":
    asyncio.run(test_error_handling())