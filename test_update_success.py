#!/usr/bin/env python3
"""Test that UPDATE operations are correctly recognized as successful"""
import asyncio
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent
import json
from unittest.mock import AsyncMock, MagicMock

load_dotenv()

async def test_update_success():
    agent = MetaAdsAgent()
    
    print("TEST: UPDATE Operation Success Recognition")
    print("=" * 70)
    
    # Simulate the exact scenario from the user's issue:
    # "update budget on brooklyn ryan castro to 200 dollars"
    
    # Mock state with successful UPDATE operation
    state = {
        "messages": [],
        "current_request": "update budget on brooklyn ryan castro to 200 dollars",
        "sdk_response": {
            "request": "update budget on brooklyn ryan castro to 200 dollars",
            "steps_executed": 3,
            "operations": [
                {"sdk_method": "search_campaigns", "parameters": {"query": "Ryan Castro"}},
                {"sdk_method": "get_adsets_for_campaign", "parameters": {"campaign_id": "120232002620350525"}},
                {"sdk_method": "update_adset_budget", "parameters": {"id": "120232176000230525", "daily_budget": 200}}
            ],
            "multi_step_results": [
                {"id": "120232002620350525", "name": "Ryan Castro Campaign"},
                [{"id": "120232176000230525", "name": "Brooklyn"}],
                {"success": True, "message": "Successfully updated budget to $200"}
            ],
            "results": {
                "step_1_results": {"id": "120232002620350525", "name": "Ryan Castro Campaign"},
                "step_2_results": [{"id": "120232176000230525", "name": "Brooklyn"}],
                "step_3_result": {"success": True, "message": "Successfully updated budget to $200"}
            }
        },
        "final_answer": "",
        "sdk_plan": {}
    }
    
    print("1. Testing pattern recognition for UPDATE operation:")
    print("-" * 50)
    
    # Test pattern recognition
    pattern = await agent.recognize_operation_pattern(state["sdk_response"])
    print(f"Pattern recognized: {pattern}")
    assert pattern == "UPDATE", f"Expected UPDATE, got {pattern}"
    print("✅ Correctly recognized UPDATE pattern")
    
    print("\n2. Testing format_response with UPDATE operation:")
    print("-" * 50)
    
    # Mock the LLM to avoid actual API calls
    original_llm = agent.llm
    agent.llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "✅ **Success**: Budget updated to $200 for Brooklyn in Ryan Castro campaign"
    agent.llm.ainvoke = AsyncMock(return_value=mock_response)
    
    # Test format_response
    result_state = await agent.format_response(state)
    
    # Check the result
    final_answer = result_state["final_answer"]
    print(f"Final answer: {final_answer}")
    
    # Verify it's a success message, not an error
    assert "Success" in final_answer or "success" in final_answer.lower(), "Should report success"
    assert "Error" not in final_answer and "ERROR" not in final_answer, "Should NOT report error"
    
    print("✅ Correctly formatted as SUCCESS (not error)")
    
    # Restore original LLM
    agent.llm = original_llm
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("✅ UPDATE operations with 'success': true are correctly recognized")
    print("✅ No false error reporting for successful updates")
    print("✅ Autonomous pattern recognition working correctly")
    print("\nTHIS FIXES THE ORIGINAL ISSUE:")
    print("- User updates budget successfully")
    print("- Bot correctly reports success, not error")
    print("- No hardcoded field checks required!")

if __name__ == "__main__":
    asyncio.run(test_update_success())