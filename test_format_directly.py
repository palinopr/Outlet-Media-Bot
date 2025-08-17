#!/usr/bin/env python3
"""Test format_response directly with successful update data"""
import asyncio
import json
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent

load_dotenv()

async def test_format_directly():
    """Test format_response with the exact successful data"""
    agent = MetaAdsAgent()
    
    # Create state with successful update response
    state = {
        "current_request": "update budget on brooklyn ryan castro to 200 dollars",
        "sdk_response": {
            "multi_step_results": [
                [{"id": "120232002620350525", "name": "The Touring Co - Ryan Castro - Sende Tour"}],
                [{"id": "120232009098430525", "name": "Sende Tour - Brooklyn"}],
                {"success": True, "adset_id": "120232009098430525", 
                 "updated_fields": {"daily_budget": 20000}, 
                 "message": "Successfully updated budget for adset 120232009098430525"}
            ],
            "operations": [
                {"sdk_method": "search_campaigns"},
                {"sdk_method": "get_adsets_for_campaign"},
                {"sdk_method": "update_adset_budget"}
            ],
            "has_errors": False
        },
        "messages": [],
        "final_answer": ""
    }
    
    print("=" * 70)
    print("TESTING FORMAT_RESPONSE DIRECTLY")
    print("=" * 70)
    
    print("\nInput SDK Response:")
    print(f"  has_errors: {state['sdk_response']['has_errors']}")
    print(f"  Last result: {state['sdk_response']['multi_step_results'][-1]}")
    
    # Call format_response directly
    result_state = await agent.format_response(state)
    
    print("\n" + "=" * 70)
    print("RESULT:")
    print("-" * 70)
    print(result_state["final_answer"])
    print("-" * 70)
    
    # Check result
    if "success" in result_state["final_answer"].lower() or "✅" in result_state["final_answer"]:
        print("\n✅ SUCCESS - format_response correctly identified success!")
    else:
        print("\n❌ FAILURE - format_response still reporting error")
        print("This is the bug we need to fix in the LLM prompt")

if __name__ == "__main__":
    asyncio.run(test_format_directly())