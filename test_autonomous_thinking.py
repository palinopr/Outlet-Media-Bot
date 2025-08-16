#!/usr/bin/env python3
"""Test agent's autonomous thinking patterns without hardcoded logic"""
import asyncio
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent
import json

load_dotenv()

async def test_autonomous_patterns():
    agent = MetaAdsAgent()
    
    print("TEST: Autonomous Thinking Patterns")
    print("=" * 70)
    
    # Test different city names to ensure no hardcoding
    test_cases = [
        "update Brooklyn budget in Ryan Castro campaign to $200",
        "update Miami budget in Ryan Castro campaign to $150",
        "update Houston budget in Ryan Castro campaign to $175",
        "update LA budget in Ryan Castro campaign to $225"
    ]
    
    for test_request in test_cases:
        print(f"\nTEST REQUEST: {test_request}")
        print("-" * 50)
        
        # Test planning phase
        state = {
            "messages": [],
            "current_request": test_request,
            "sdk_response": None,
            "final_answer": "",
            "sdk_plan": {}
        }
        
        # Get the plan
        result = await agent.understand_request(state)
        plan = result.get("sdk_plan", {})
        
        print("AGENT'S UNDERSTANDING:")
        print(f"  Intent: {plan.get('intent', 'unknown')}")
        
        if "operations" in plan:
            print("  Operations planned:")
            for i, op in enumerate(plan["operations"]):
                print(f"    {i+1}. {op['sdk_method']}")
                if "iterate_on" in op:
                    print(f"       (iterating on results from step {op['iterate_on'].split('_')[-1]})")
                if "uses_result_from" in op:
                    print(f"       (using result from step {op['uses_result_from'] + 1})")
        
        # Check if the agent is using efficient patterns
        if "operations" in plan and len(plan["operations"]) >= 2:
            second_op = plan["operations"][1].get("sdk_method", "")
            
            if second_op == "get_adsets_for_campaign":
                print("  ✅ Using EFFICIENT pattern (get_adsets_for_campaign)")
            elif second_op == "search_adsets":
                print("  ❌ Using INEFFICIENT pattern (search_adsets)")
            else:
                print(f"  ⚠️ Using method: {second_op}")
        
        # Check for hardcoded strings in the plan
        plan_str = json.dumps(plan)
        hardcoded_cities = ["brooklyn", "miami", "houston", "los angeles"]
        found_hardcoded = False
        for city in hardcoded_cities:
            if city in plan_str.lower():
                print(f"  ⚠️ WARNING: Found hardcoded '{city}' in plan!")
                found_hardcoded = True
        
        if not found_hardcoded:
            print("  ✅ No hardcoded city names found - using pattern matching!")
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("The agent should be using pattern matching to identify items,")
    print("not hardcoding specific strings like 'brooklyn' or 'miami'.")
    print("This allows it to work with ANY city or item name.")

if __name__ == "__main__":
    asyncio.run(test_autonomous_patterns())