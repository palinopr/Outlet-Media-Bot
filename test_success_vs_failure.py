#!/usr/bin/env python3
"""Test agent handling of success vs failure scenarios"""
import asyncio
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent

load_dotenv()

async def test_scenarios():
    agent = MetaAdsAgent()
    
    print("SCENARIO 1: Request with non-existent campaign")
    print("=" * 70)
    response1 = await agent.process_request("update budget for FAKECAMPAIGN brooklyn to $300")
    print(response1)
    
    # Check response
    if "error" in response1.lower() or "unable" in response1.lower() or "not found" in response1.lower():
        print("\n✅ Correctly reported error for non-existent campaign")
    else:
        print("\n❌ Failed to report error properly")
    
    print("\n" + "=" * 70)
    print("\nSCENARIO 2: Request with typo in city name")
    print("=" * 70)
    response2 = await agent.process_request("show me spend for Ryan Castro campaign in FAKECITY")
    print(response2)
    
    # Check response
    if "$0" in response2 or "N/A" in response2:
        print("\n⚠️ Shows zero or N/A (acceptable)")
    elif "unable" in response2.lower() or "not found" in response2.lower():
        print("\n✅ Correctly reported data not found")
    else:
        amounts = [amt for amt in ["$385", "$317", "$286"] if amt in response2]
        if amounts:
            print(f"\n❌ May be showing hallucinated values: {amounts}")
        else:
            print("\n✅ Not showing fake values")
    
    print("\n" + "=" * 70)
    print("\nSCENARIO 3: Valid request (if API is working)")
    print("=" * 70)
    response3 = await agent.process_request("show me the total spend for Ryan Castro campaign")
    print(response3)
    
    # Check if response has real data or properly reports unavailability
    if "unable" in response3.lower():
        print("\n✅ Properly reported data unavailable")
    elif "$" in response3:
        print("\n✅ Shows monetary values (check if they're real)")
    else:
        print("\n⚠️ Unclear response")

if __name__ == "__main__":
    asyncio.run(test_scenarios())