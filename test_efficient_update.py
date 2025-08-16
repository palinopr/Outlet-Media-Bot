#!/usr/bin/env python3
"""Test if agent uses efficient API approach"""
import asyncio
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent
import json

load_dotenv()

async def test_efficient_approach():
    agent = MetaAdsAgent()
    
    print("TEST: Efficient Budget Update Approach")
    print("=" * 70)
    
    # Create a mock state to see what plan the agent generates
    state = {
        "messages": [],
        "current_request": "update budget for Brooklyn in Ryan Castro campaign to $200",
        "sdk_response": None,
        "final_answer": "",
        "sdk_plan": {}
    }
    
    # Just test the planning phase
    result = await agent.understand_request(state)
    
    plan = result.get("sdk_plan", {})
    
    print("AGENT'S PLAN:")
    print(json.dumps(plan, indent=2))
    
    print("\n" + "=" * 70)
    print("ANALYSIS:")
    
    if "operations" in plan:
        ops = plan["operations"]
        if len(ops) >= 2:
            second_op = ops[1].get("sdk_method", "")
            
            if second_op == "get_adsets_for_campaign":
                print("✅ EFFICIENT: Agent chose get_adsets_for_campaign")
                print("   This will only fetch adsets for Ryan Castro campaign")
            elif second_op == "search_adsets":
                print("❌ INEFFICIENT: Agent chose search_adsets")
                print("   This will fetch ALL adsets in the account (rate limit risk)")
            else:
                print(f"⚠️ Unexpected second operation: {second_op}")
    
    # Now test actual execution
    print("\n" + "=" * 70)
    print("\nEXECUTING REQUEST:")
    response = await agent.process_request("update Brooklyn budget in Ryan Castro campaign to $200")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_efficient_approach())