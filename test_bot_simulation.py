#!/usr/bin/env python3
"""Debug what SDK response the agent sees"""
import asyncio
import json
from dotenv import load_dotenv
from agents.meta_ads_agent import MetaAdsAgent
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

async def test_bot_flow():
    """Debug the SDK response the agent gets"""
    agent = MetaAdsAgent()
    
    # Monkey-patch ALL nodes to trace execution
    original_understand = agent.understand_request
    async def trace_understand(state):
        print("\n>>> UNDERSTAND_REQUEST called")
        result = await original_understand(state)
        if 'final_answer' in result and result['final_answer']:
            print(f"    UNDERSTAND SET final_answer: {result['final_answer'][:100]}")
        return result
    agent.understand_request = trace_understand
    
    original_review = agent.review_thinking
    async def trace_review(state):
        print("\n>>> REVIEW_THINKING called")
        result = await original_review(state)
        if 'final_answer' in result and result['final_answer']:
            print(f"    REVIEW SET final_answer: {result['final_answer'][:100]}")
        return result
    agent.review_thinking = trace_review
    
    original_verify = agent.verify_execution
    async def trace_verify(state):
        print("\n>>> VERIFY_EXECUTION called")
        result = await original_verify(state)
        if 'final_answer' in result and result['final_answer']:
            print(f"    VERIFY SET final_answer: {result['final_answer'][:100]}")
        return result
    agent.verify_execution = trace_verify
    
    # Monkey-patch execute_sdk_call to see what it returns
    original_execute = agent.execute_sdk_call
    
    async def debug_execute_sdk(state):
        print("\n" + "=" * 70)
        print("EXECUTE_SDK_CALL CALLED")
        print("-" * 70)
        
        # Print plan
        if 'plan' in state:
            print("\nPLAN:")
            print(json.dumps(state['plan'], indent=2))
        
        # Call original
        result_state = await original_execute(state)
        
        # Print SDK response
        if 'sdk_response' in result_state:
            print("\nSDK_RESPONSE SET TO:")
            sdk_resp = result_state['sdk_response']
            print(json.dumps(sdk_resp, indent=2) if isinstance(sdk_resp, dict) else str(sdk_resp))
            
            # Check for error field
            if isinstance(sdk_resp, dict) and 'error' in sdk_resp:
                print("\n⚠️ ERROR FIELD FOUND IN SDK_RESPONSE!")
        
        print("=" * 70)
        
        return result_state
    
    agent.execute_sdk_call = debug_execute_sdk
    
    # Also monkey-patch format_response to see what data it gets
    original_format = agent.format_response
    
    async def debug_format_response(state):
        print("\n" + "=" * 70)
        print("FORMAT_RESPONSE CALLED")
        print("-" * 70)
        
        sdk_response = state.get("sdk_response", {})
        
        # Check what we're looking for
        has_errors = sdk_response.get("has_errors", None)
        print(f"\nhas_errors field: {has_errors}")
        
        # Look for success in results
        if "multi_step_results" in sdk_response:
            for i, result in enumerate(sdk_response["multi_step_results"]):
                if isinstance(result, dict) and "success" in result:
                    print(f"Result {i} has success: {result['success']}")
                    if "message" in result:
                        print(f"  Message: {result['message']}")
        
        # Call original
        result = await original_format(state)
        
        print("\nFORMAT_RESPONSE RESULT:")
        print(result.get("final_answer", ""))
        
        return result
    
    agent.format_response = debug_format_response
    
    # Add tracing to see which nodes are called
    nodes_called = []
    original_process = agent.process_request
    
    async def trace_process(request):
        # Trace graph execution
        print("\nTRACING GRAPH EXECUTION:")
        print("-" * 70)
        
        # Get initial state
        initial_state = {
            "messages": [],
            "current_request": request,
            "sdk_response": None,
            "final_answer": "",
            "sdk_plan": {}
        }
        
        # Run WITHOUT LangSmith tracing to see actual execution
        try:
            print("Invoking graph directly without LangSmith...")
            # Directly invoke without tracing
            result = await agent.graph.ainvoke(initial_state)
            print(f"Graph returned, final_answer present: {'final_answer' in result}")
            if 'final_answer' in result:
                print(f"Final answer: {result['final_answer']}")
            print(f"SDK response: {result.get('sdk_response', 'None')}")
            print(f"SDK plan: {result.get('sdk_plan', 'None')}")
            return result.get("final_answer", "I couldn't process your request.")
        except Exception as e:
            print(f"ERROR IN GRAPH: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ **Error**: Unable to update budget due to API error."
    
    agent.process_request = trace_process
    
    print("=" * 70)
    print("DEBUGGING SDK RESPONSE - Budget Update")
    print("=" * 70)
    
    # Simulate the exact request
    request = "update budget on brooklyn ryan castro to 200 dollars"
    print(f"\nRequest: {request}")
    
    # Process through the agent
    result = await agent.process_request(request)
    
    print("\n" + "=" * 70)
    print("FINAL RESPONSE FROM AGENT:")
    print("-" * 70)
    print(result)
    print("-" * 70)
    
    print("\n" + "=" * 70)
    print("ANALYSIS:")
    if "success" in result.lower() or "✅" in result:
        print("✅ Bot correctly reported SUCCESS")
    elif "error" in result.lower() or "❌" in result or "🔴" in result:
        print("❌ Bot incorrectly reported ERROR")
        print("   This is the issue we need to fix!")
    else:
        print("⚠️ Unclear response")

if __name__ == "__main__":
    asyncio.run(test_bot_flow())