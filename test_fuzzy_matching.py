#!/usr/bin/env python3
"""
Test fuzzy matching functionality with typos
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.meta_ads_agent import MetaAdsAgent
from dotenv import load_dotenv

load_dotenv()

async def test_fuzzy_matching():
    """Test that the agent can handle typos in adset names"""
    
    print("=" * 60)
    print("TESTING FUZZY MATCHING WITH TYPOS")
    print("=" * 60)
    
    # Initialize agent
    agent = MetaAdsAgent()
    
    # Test cases with typos
    test_cases = [
        {
            "request": "update budget on brroklyn ryan castro to 100",
            "expected": "Brooklyn",
            "description": "Double 'r' typo in Brooklyn"
        },
        {
            "request": "update budget on brookln ryan castro to 100",
            "expected": "Brooklyn",
            "description": "Missing 'y' in Brooklyn"
        },
        {
            "request": "update budget on broklin ryan castro to 100",
            "expected": "Brooklyn",
            "description": "Missing 'o' and 'y' replaced with 'i'"
        },
        {
            "request": "update budget on miami ryan castro to 100",
            "expected": "Miami",
            "description": "Exact match (no typo)"
        }
    ]
    
    for test in test_cases:
        print(f"\n📝 Test: {test['description']}")
        print(f"   Request: '{test['request']}'")
        print(f"   Expected to match: {test['expected']}")
        
        # Create state for testing
        state = {
            "messages": [],
            "current_request": test["request"],
            "thinking_history": []
        }
        
        # Test the thinking pattern for similarity
        similarity_context = f"""
        Is 'brroklyn' likely a typo or variation of 'Brooklyn'?
        Consider common typos like double letters, swapped letters, missing letters.
        Calculate similarity score 0-100.
        """
        
        thought = await agent.think(similarity_context)
        
        print(f"   Similarity score: {thought.get('similarity_score', 'N/A')}")
        print(f"   Confidence: {thought.get('confidence_level', 'N/A')}")
        print(f"   Needs clarification: {thought.get('needs_clarification', False)}")
        print(f"   Decision: {thought.get('decision', 'N/A')}")
        
        # Test with actual SDK call simulation
        print(f"\n   Testing full flow...")
        
        # Simulate having adsets from previous step
        mock_adsets = [
            {"id": "120232176000230525", "name": "Sende Tour - Retargeting"},
            {"id": "120232009098430525", "name": "Sende Tour - Brooklyn"},
            {"id": "120232009098430526", "name": "Sende Tour - Miami"}
        ]
        
        # Test the matching logic
        words = test["request"].split()
        best_match = None
        best_confidence = 0
        
        for adset in mock_adsets:
            adset_name = adset["name"].lower()
            for word in words:
                if len(word) > 2:
                    if word.lower() in adset_name:
                        print(f"   ✅ Exact match found: '{word}' in '{adset['name']}'")
                        best_match = adset
                        best_confidence = 100
                        break
                    else:
                        # Simulate fuzzy matching thought
                        fuzzy_context = f"Is '{word}' likely a typo of any part of '{adset_name}'?"
                        fuzzy_thought = await agent.think(fuzzy_context)
                        score = fuzzy_thought.get('similarity_score', 0)
                        if score > 70:
                            print(f"   🔍 Fuzzy match: '{word}' ~ '{adset['name']}' (score: {score})")
                            if score > best_confidence:
                                best_match = adset
                                best_confidence = score
        
        if best_match and best_confidence >= 70:
            print(f"   ✨ Selected: {best_match['name']} (confidence: {best_confidence}%)")
            if test["expected"] in best_match["name"]:
                print(f"   ✅ CORRECT MATCH!")
            else:
                print(f"   ❌ WRONG MATCH - Expected {test['expected']}")
        else:
            print(f"   ⚠️ No confident match (best: {best_confidence}%)")
            print(f"   Would ask for clarification instead of defaulting")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_fuzzy_matching())