#!/usr/bin/env python3
"""Test if agent properly validates and uses real data"""
import asyncio
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent

load_dotenv()

async def test_agent():
    agent = MetaAdsAgent()
    
    # Test 1: Get metrics by city (should use real data)
    print("TEST 1: Metrics by City")
    print("=" * 70)
    request = "show me the spend and ROAS for Ryan Castro's campaign by city"
    response = await agent.process_request(request)
    print(response)
    
    # Check if response contains real values
    real_values = ['52.91', '384.87', '317.29', '286.12', '242.79', '336.10']
    found_real = [v for v in real_values if v in response]
    
    print("\n" + "=" * 70)
    if found_real:
        print(f"✅ PASS: Found {len(found_real)} real values: {found_real}")
    else:
        print("❌ FAIL: No real values found - agent may be hallucinating!")
    
    print("\n" + "=" * 70)
    # Test 2: Budget update (should verify success)
    print("\nTEST 2: Budget Update")
    print("=" * 70)
    request2 = "update Brooklyn budget in Ryan Castro campaign to $200"
    response2 = await agent.process_request(request2)
    print(response2)
    
    # Check if response properly reports success or failure
    if "successfully" in response2.lower() or "updated" in response2.lower():
        print("\n✅ Agent reported update status")
    else:
        print("\n⚠️ Agent did not clearly report update status")

if __name__ == "__main__":
    asyncio.run(test_agent())