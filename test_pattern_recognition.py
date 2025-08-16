#!/usr/bin/env python3
"""Test the agent's pattern recognition in format_response"""
import asyncio
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent
import json

load_dotenv()

async def test_pattern_recognition():
    agent = MetaAdsAgent()
    
    print("TEST: Operation Pattern Recognition")
    print("=" * 70)
    
    # Test UPDATE pattern recognition
    print("\n1. Testing UPDATE pattern recognition:")
    print("-" * 50)
    
    update_response = {
        "operations": [
            {"sdk_method": "search_campaigns"},
            {"sdk_method": "get_adsets_for_campaign"},
            {"sdk_method": "update_adset_budget"}
        ],
        "multi_step_results": [
            {"id": "12345", "name": "Ryan Castro"},
            [{"id": "67890", "name": "Brooklyn"}],
            {"success": True, "message": "Successfully updated budget to $200"}
        ]
    }
    
    pattern = await agent.recognize_operation_pattern(update_response)
    print(f"Response with 'update_adset_budget': {pattern}")
    assert pattern == "UPDATE", f"Expected UPDATE, got {pattern}"
    print("✅ Correctly recognized UPDATE pattern")
    
    # Test QUERY pattern recognition
    print("\n2. Testing QUERY pattern recognition:")
    print("-" * 50)
    
    query_response = {
        "operations": [
            {"sdk_method": "search_campaigns"},
            {"sdk_method": "get_adsets_for_campaign"},
            {"sdk_method": "get_adset_insights"}
        ],
        "multi_step_results": [
            {"id": "12345", "name": "Ryan Castro"},
            [{"id": "67890", "name": "Brooklyn"}, {"id": "11111", "name": "Miami"}],
            [
                {"spend": 388.08, "impressions": 5000},
                {"spend": 245.23, "impressions": 3000}
            ]
        ]
    }
    
    pattern = await agent.recognize_operation_pattern(query_response)
    print(f"Response with 'get_adset_insights': {pattern}")
    assert pattern == "QUERY", f"Expected QUERY, got {pattern}"
    print("✅ Correctly recognized QUERY pattern")
    
    # Test mixed operations
    print("\n3. Testing pattern recognition without operations list:")
    print("-" * 50)
    
    success_only_response = {
        "multi_step_results": [
            {"success": True, "updated": True}
        ]
    }
    
    pattern = await agent.recognize_operation_pattern(success_only_response)
    print(f"Response with success indicator: {pattern}")
    assert pattern == "UPDATE", f"Expected UPDATE, got {pattern}"
    print("✅ Correctly recognized UPDATE from success pattern")
    
    # Test data array pattern
    print("\n4. Testing data array pattern:")
    print("-" * 50)
    
    data_array_response = {
        "multi_step_results": [
            [
                {"name": "Item 1", "value": 100},
                {"name": "Item 2", "value": 200},
                {"name": "Item 3", "value": 300}
            ]
        ]
    }
    
    pattern = await agent.recognize_operation_pattern(data_array_response)
    print(f"Response with data array: {pattern}")
    assert pattern == "QUERY", f"Expected QUERY, got {pattern}"
    print("✅ Correctly recognized QUERY from data array pattern")
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("✅ All pattern recognition tests passed!")
    print("✅ Agent correctly identifies UPDATE vs QUERY patterns")
    print("✅ No hardcoded field names required!")

if __name__ == "__main__":
    asyncio.run(test_pattern_recognition())