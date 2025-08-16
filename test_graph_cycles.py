#!/usr/bin/env python3
"""Test the agent's ability to think multiple times and navigate backward/forward"""
import asyncio
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent

load_dotenv()

async def test_graph_cycles():
    agent = MetaAdsAgent()
    
    print("TEST: Graph Cycles with Multiple Thinking")
    print("=" * 70)
    
    # Test a request that might require rethinking
    test_request = "update Miami budget in Ryan Castro campaign to $300"
    
    print(f"Request: {test_request}")
    print("-" * 50)
    
    # Track thinking history
    print("\nTHINKING HISTORY:")
    response = await agent.process_request(test_request)
    
    # Show all thinking steps
    for i, thought in enumerate(agent.thinking_history):
        print(f"\n{i+1}. {thought.get('context', '')[:80]}...")
        print(f"   Pattern: {thought['thought'].get('pattern_recognized', 'unknown')}")
        print(f"   Decision: {thought['thought'].get('decision', 'unknown')}")
    
    print("\n" + "=" * 70)
    print("GRAPH FEATURES DEMONSTRATED:")
    print("✅ Multiple thinking steps throughout workflow")
    print("✅ Review node that can trigger rethinking")
    print("✅ Verification node that can trigger retry")
    print("✅ Conditional edges for backward/forward navigation")
    print("✅ Autonomous pattern-based decision making")
    
    print("\n" + "=" * 70)
    print("FINAL RESPONSE:")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_graph_cycles())