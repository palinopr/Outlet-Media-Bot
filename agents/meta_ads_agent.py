"""
Meta Ads Agent using LangGraph v2.0.1
Simple agent that can think about requests and use Meta SDK tools
Enhanced with multi-step planning and autonomous operation chaining
"""
import os
import logging
import json
import inspect
from typing import Dict, Any, List, TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.tracers.context import tracing_v2_enabled
from tools.meta_sdk import MetaAdsSDK

# Enable tracing if configured
if os.getenv("LANGCHAIN_TRACING_V2"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Simple state for the agent"""
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    current_request: str
    sdk_response: Any
    final_answer: str
    sdk_plan: Dict[str, Any]  # Add this field to fix the error


class MetaAdsAgent:
    """Simple Meta Ads agent that can think and use tools"""
    
    def __init__(self):
        # Initialize Meta SDK
        self.sdk = MetaAdsSDK()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize thinking history
        self.thinking_history = []
        
        # Create the graph
        self.graph = self._create_graph()
    
    async def think(self, context: str, previous_thought: str = None) -> Dict[str, Any]:
        """
        Autonomous thinking method that can be called multiple times.
        Returns a thought process and decision.
        """
        thinking_prompt = """You are an autonomous thinking module for a Meta Ads agent.
        
Your role is to think through problems step by step, recognize patterns, and make decisions.

THINKING PRINCIPLES:
- Break down complex problems into simple patterns
- Recognize similarities between different requests
- Learn from context, don't memorize specifics
- Question your assumptions and revise if needed
- Think about WHY something works, not just WHAT works

PATTERN RECOGNITION:
- When you see a request, think: "What pattern does this follow?"
- Examples of patterns:
  • "Find X and update it" → Search pattern + Update pattern
  • "Get metrics for Y" → Data retrieval pattern
  • "Compare A and B" → Comparison pattern
- Apply patterns broadly, not to specific cases

DECISION MAKING:
- Based on your thinking, decide:
  • What needs to be done?
  • What's the most efficient approach?
  • What could go wrong?
  • How to verify success?

Context: {context}
Previous thought: {previous_thought}

Think through this and return your reasoning as JSON:
{{
    "pattern_recognized": "what pattern does this follow",
    "key_insights": ["insight 1", "insight 2"],
    "decision": "what to do based on this thinking",
    "potential_issues": ["issue 1", "issue 2"],
    "verification_approach": "how to verify this worked"
}}"""

        messages = [
            SystemMessage(content=thinking_prompt.format(
                context=context,
                previous_thought=previous_thought or "None"
            ))
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            # Parse thinking response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            thought = json.loads(content)
            
            # Store in thinking history
            self.thinking_history.append({
                "context": context,
                "thought": thought,
                "timestamp": __import__('time').time()
            })
            
            logger.info(f"Thinking: {thought.get('pattern_recognized', 'unknown pattern')}")
            return thought
        except Exception as e:
            logger.error(f"Thinking error: {e}")
            return {
                "pattern_recognized": "error in thinking",
                "decision": "proceed with caution",
                "error": str(e)
            }
    
    def _create_graph(self):
        """Create the LangGraph workflow with thinking cycles"""
        workflow = StateGraph(AgentState)
        
        # Add nodes - now with a thinking review node
        workflow.add_node("understand_request", self.understand_request)
        workflow.add_node("review_thinking", self.review_thinking)
        workflow.add_node("execute_sdk_call", self.execute_sdk_call)
        workflow.add_node("verify_execution", self.verify_execution)
        workflow.add_node("format_response", self.format_response)
        
        # Add edges with conditional routing
        workflow.set_entry_point("understand_request")
        
        # After understanding, review the thinking
        workflow.add_edge("understand_request", "review_thinking")
        
        # From review, decide whether to proceed or rethink
        workflow.add_conditional_edges(
            "review_thinking",
            self.should_proceed_or_rethink,
            {
                "proceed": "execute_sdk_call",
                "rethink": "understand_request"
            }
        )
        
        # After execution, verify if it worked
        workflow.add_edge("execute_sdk_call", "verify_execution")
        
        # From verification, decide whether to retry or format response
        workflow.add_conditional_edges(
            "verify_execution",
            self.should_retry_or_continue,
            {
                "retry": "understand_request",
                "continue": "format_response"
            }
        )
        
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def review_thinking(self, state: AgentState) -> AgentState:
        """Review the thinking and decide if we should proceed or rethink"""
        plan = state.get("sdk_plan", {})
        
        # Think about whether the plan makes sense
        review_context = f"Reviewing plan: {plan.get('intent', 'unknown')}. Operations: {len(plan.get('operations', []))} steps."
        review_thought = await self.think(review_context)
        
        # Store review in state
        state["messages"].append(
            AIMessage(content=f"Review: {review_thought.get('decision', 'proceeding')}")
        )
        
        return state
    
    def should_proceed_or_rethink(self, state: AgentState) -> Literal["proceed", "rethink"]:
        """Decide whether to proceed with execution or rethink the plan"""
        # Check if we've thought enough times
        thinking_count = len([t for t in self.thinking_history if "review" in str(t.get("context", ""))])
        
        # If we've reviewed more than 2 times, proceed to avoid infinite loops
        if thinking_count > 2:
            logger.info("Maximum thinking iterations reached, proceeding")
            return "proceed"
        
        # Check if the last review identified issues
        if self.thinking_history and "issue" in str(self.thinking_history[-1].get("potential_issues", [])):
            logger.info("Issues identified in review, rethinking")
            return "rethink"
        
        return "proceed"
    
    async def verify_execution(self, state: AgentState) -> AgentState:
        """Verify if the execution was successful"""
        sdk_response = state.get("sdk_response", {})
        
        # Think about the execution results
        if isinstance(sdk_response, dict) and "has_errors" in sdk_response:
            verification_context = f"Execution had errors: {sdk_response.get('has_errors')}"
        else:
            verification_context = "Execution completed, verifying results"
        
        verification_thought = await self.think(verification_context)
        
        # Store verification in state
        state["messages"].append(
            AIMessage(content=f"Verification: {verification_thought.get('verification_approach', 'checking')}")
        )
        
        return state
    
    def should_retry_or_continue(self, state: AgentState) -> Literal["retry", "continue"]:
        """Decide whether to retry execution or continue to formatting"""
        sdk_response = state.get("sdk_response", {})
        
        # Check retry count to avoid infinite loops
        retry_count = len([m for m in state["messages"] if isinstance(m.content, str) and "retry" in m.content.lower()])
        if retry_count >= 2:
            logger.info("Maximum retries reached, continuing")
            return "continue"
        
        # Check if there were critical errors
        if isinstance(sdk_response, dict):
            if sdk_response.get("has_errors") and sdk_response.get("has_errors") == True:
                # Check if all operations failed
                if "multi_step_results" in sdk_response:
                    results = sdk_response["multi_step_results"]
                    error_count = sum(1 for r in results if isinstance(r, dict) and "error" in r)
                    if error_count == len(results):
                        logger.info("All operations failed, retrying")
                        return "retry"
        
        return "continue"
    
    async def recognize_operation_pattern(self, sdk_response: Dict[str, Any]) -> str:
        """
        AUTONOMOUS PATTERN RECOGNITION - Recognizes operation type from response
        No hardcoded field checks - pure pattern recognition
        """
        # Analyze operations if present - check LAST operation as it determines the type
        if "operations" in sdk_response:
            operations = sdk_response["operations"]
            
            # Look for patterns in operation names - use word boundaries
            # Check for common prefixes/patterns in Meta SDK method names
            update_patterns = ["update_", "set_", "modify_", "change_", "edit_"]
            query_patterns = ["get_", "search_", "fetch_", "list_", "retrieve_", "_insights", "_metrics"]
            
            # Check the LAST operation, as it determines the overall type
            if operations:
                last_op = operations[-1]
                method_name = last_op.get("sdk_method", "").lower()
                
                # Check for QUERY patterns FIRST (more specific)
                if any(pattern in method_name for pattern in query_patterns):
                    return "QUERY"
                
                # Check for UPDATE patterns after QUERY
                if any(pattern in method_name for pattern in update_patterns):
                    return "UPDATE"
        
        # Analyze results structure if no operations
        if "multi_step_results" in sdk_response:
            results = sdk_response["multi_step_results"]
            
            # Look for success/error patterns (typical of UPDATE operations)
            for result in results:
                if isinstance(result, dict):
                    if "success" in result or "updated" in result:
                        return "UPDATE"
                    if "error" in result:
                        return "ERROR"
            
            # If we have arrays of data, likely a QUERY
            if any(isinstance(r, list) for r in results):
                return "QUERY"
        
        return "UNKNOWN"
    
    async def understand_request(self, state: AgentState) -> AgentState:
        """Understand what the user is asking for"""
        request = state["current_request"]
        
        # THINK FIRST: What pattern does this request follow?
        thought = await self.think(f"User request: {request}")
        logger.info(f"Initial thinking complete: {thought.get('pattern_recognized')}")
        
        # Use LLM to understand the request and plan SDK call
        # Get available SDK methods dynamically
        sdk_methods = [method for method in dir(self.sdk) if not method.startswith('_')]
        
        # Get actual method signatures dynamically using introspection
        method_signatures = []
        for method_name in sdk_methods:
            if hasattr(self.sdk, method_name):
                method = getattr(self.sdk, method_name)
                if callable(method):
                    sig = inspect.signature(method)
                    params = []
                    for param_name, param in sig.parameters.items():
                        if param_name != 'self':
                            if param.default != inspect.Parameter.empty:
                                params.append(f"{param_name}={repr(param.default)}")
                            else:
                                params.append(param_name)
                    method_signatures.append(f"• {method_name}({', '.join(params)})")
        
        # Build the system prompt without f-string for the JSON examples
        system_prompt = """You are an intelligent Meta Ads assistant. 

AVAILABLE SDK METHODS (discovered dynamically):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""" + '\n'.join(method_signatures) + """

THINKING PATTERNS (How to approach problems):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 AUTONOMOUS THINKING PRINCIPLES:
   - Learn patterns, not specific solutions
   - Think: "What type of problem is this?"
   - Apply general patterns to specific cases
   - Never rely on hardcoded strings or values
   - Adapt your approach based on the data you receive
   - Example thought process:
     • "User wants to update something"
     • "I need to find that thing first"
     • "Then I need to update it"
     • "Then I need to verify it worked"
   - This pattern works for ANY update task

📊 UNDERSTANDING DATA STRUCTURES:
   - Methods return data in different shapes:
     • Single item: {"id": "123", "name": "example"}
     • List of items: [{"id": "1"}, {"id": "2"}, {"id": "3"}]
     • Empty or error: {} or {"error": "message"}
   - Lists contain multiple items, each with properties
   - Common properties: 'id' (identifier), 'name' (label)
   - Think: What shape will this method return?

🔍 DISCOVERY PATTERN:
   - Look at method names to understand their purpose
   - Methods starting with 'search_' find specific items
   - Methods starting with 'get_' retrieve data
   - Methods with 'insights' return metrics (spend, ROAS, clicks)
   - Methods with 'adset' work with cities/locations
   - Understand relationships: campaigns contain adsets, adsets represent cities
   - get_campaign_insights = overall campaign metrics
   - get_adset_insights = metrics for specific city/location

⚡ EFFICIENT API USAGE PATTERN:
   - PREFER hierarchical navigation over global searches
   - If you know the campaign, use get_adsets_for_campaign NOT search_adsets
   - search_adsets loads ALL adsets (expensive, hits rate limits)
   - get_adsets_for_campaign loads ONLY that campaign's adsets (efficient)
   - Think: "What's the most direct path with fewest API calls?"
   - Example: To update Brooklyn in Ryan Castro campaign:
     INEFFICIENT: search_campaigns → search_adsets (all) → update
     EFFICIENT: search_campaigns → get_adsets_for_campaign → update
   - Fewer API calls = Less chance of rate limits

🧩 UNDERSTANDING PARAMETERS:
   - param=None means optional - you can omit it
   - 'fields' parameters usually expect a list: ['field1', 'field2']
   - NEVER pass comma-separated strings like "field1,field2" 
   - When in doubt, omit optional parameters and use defaults
   - Look at parameter names for hints: 'fields' = list, 'query' = string

💡 UNDERSTANDING API DATA PATTERNS:
   - APIs may return monetary values in different units
   - Meta API: READ operations return dollars, WRITE operations expect cents
   - Always validate data magnitude: $0.27 for active campaign? Probably wrong
   - If values seem 100x too small/large, check unit conversion
   - Learn from patterns: consistent small values = likely unit issue
   - Monetary fields like 'spend' often need unit awareness

🔧 UNDERSTANDING SDK METHOD PATTERNS:
   - Read method docstrings - they explain parameter expectations
   - Update methods often say "values in dollars" - pass dollars directly
   - SDK handles conversions internally - don't double-convert
   - Example: update_adset_budget expects dollars, converts to cents internally
   - When updating budget to $200, pass 200, NOT 20000
   - Trust the SDK to handle unit conversions

🎯 UNDERSTANDING USER INTENT:
   - "cities" = adsets in Meta Ads
   - "spend/ROAS/performance" = insights data
   - "active/paused" = status filtering
   - When user asks for specific names, use search methods
   - When user asks for metrics, use insights methods
   - "by city" or "per city" = need BREAKDOWN, not total
   - "for each city" = iterate through adsets
   - "total" or "overall" = campaign-level is enough
   - Plural + "tell me" = user wants details for ALL items

💰 BUDGET UPDATE PATTERNS:
   - "Update budget to $X" = user wants daily budget of X dollars
   - Pass dollar amounts directly to update methods
   - SDK methods handle dollar→cent conversion internally
   - Example: "update [location] to $200" → update_adset_budget(daily_budget=200)
   - Never multiply by 100 yourself - SDK does this
   - EFFICIENT PATH: If updating adset in specific campaign:
     1. Find campaign → 2. Get its adsets → 3. Find target → 4. Update
     NOT: Find campaign → Search ALL adsets → Update
   - VERIFY SUCCESS: Check response has success=True before confirming
   - If update fails, report the error, don't claim success
   - After update, you may want to fetch updated values to confirm

🎯 ITEM SELECTION PATTERN (Finding specific items in lists):
   - When user mentions a specific item by name (city, campaign, adset)
   - And you have a list of items from previous step
   - Think: "Which item in this list matches what the user asked for?"
   - Pattern recognition approach:
     • Extract identifying words from user request (proper nouns, capitals)
     • Iterate through list items
     • Match request keywords against item names
     • Select the matching item's ID for operations
   - Example: User says "update Miami budget"
     • You have list: [{name: "Tour - Miami", id: "123"}, {name: "Tour - LA", id: "456"}]
     • Extract "Miami" from request
     • Find item with "Miami" in name
     • Use ID "123" for update operation
   - This pattern works for ANY selection task:
     • Selecting campaigns by name
     • Finding specific adsets/cities
     • Choosing ads to update
   - NO HARDCODING: Never hardcode specific strings like "brooklyn" or "miami"
   - Think generically: "How do I match user intent to available items?"

📊 INSIGHTS PATTERN - DATE SELECTION:
   - Insights methods accept date_preset parameter
   - Valid values: "today", "yesterday", "last_7d", "last_14d", "last_28d", "last_30d", "last_90d", "maximum"
   - IMPORTANT DATE LOGIC:
     • User doesn't specify time = use "maximum" (all available data)
     • "recent" or "this week" = use "last_7d"
     • "this month" = use "last_30d"
     • "today" = use "today"
     • "all time" or "total" = use "maximum"
   - NEVER use "lifetime" - it's invalid and causes errors
   - When in doubt, use "maximum" to get the most complete picture
   - For city-level metrics, use get_adset_insights if available
   - Don't specify fields parameter unless needed - defaults work well

🔍 CONTEXT-AWARE PATTERN MATCHING:
   - Extract context from user requests dynamically
   - Don't hardcode expectations about specific words
   - Pattern: "update [SOMETHING] in [SOMEWHERE] to [VALUE]"
     • SOMETHING = what to update (extract from request)
     • SOMEWHERE = where to find it (extract from request)  
     • VALUE = new value (extract from request)
   - Apply this pattern to ANY update request
   - Let the context determine the specifics
   - Examples of pattern application:
     • "update Miami budget" → SOMETHING=budget, SOMEWHERE=Miami
     • "update campaign status" → SOMETHING=status, SOMEWHERE=campaign
     • "update LA daily spend" → SOMETHING=daily spend, SOMEWHERE=LA

🔗 MULTI-STEP THINKING:
   - Break complex requests into steps
   - Each step gets you closer to the answer
   - Use results from one step in the next (result_from_X)
   - Think about what data you need and which methods provide it

🧠 PROBLEM SOLVING APPROACH:
   1. Understand what the user is asking for
   2. Identify which data points you need
   3. Find methods that provide that data
   4. Plan the sequence of calls
   5. Handle results intelligently

🔁 EXPRESSING ITERATION INTENT:
   - When you need data for EACH item in a list:
     • Use "iterate_on": "result_from_X" in your operation
     • This tells the system to run this operation for EACH item
   - Example: User asks "spend by city" and step 2 returns 6 cities:
     • Add "iterate_on": "result_from_1" to get insights for EACH city
   - The system automatically handles the iteration
   - You just express WHAT you want, not HOW to loop

📝 DYNAMIC THINKING PATTERN:
   - Analyze what the user wants
   - Identify what data structure you'll get (single item vs list)
   - Decide if you need details for each item
   - Use "iterate_on" when you need to process each item
   - Let the system handle the execution details

💡 WHEN USER ASKS FOR METRICS BY CITY:
   - Cities are adsets in Meta Ads
   - "by city" = need metrics for EACH adset separately
   - Plan: get adsets, then iterate to get insights for each
   - Use "iterate_on" to express this intent

🔄 HANDLING EMPTY RESULTS:
   - If insights return empty, try different date_preset
   - Start with "last_7d" for recent data
   - Try "lifetime" for all-time data
   - Explain to user what you tried

⚠️ DATA VALIDATION THINKING:
   - ALWAYS verify data exists before using it
   - Check data structure: Does 'city_metrics' exist? Is it an array?
   - If data is missing or empty, SAY SO - never make up values
   - Navigate JSON carefully: data['results']['city_metrics'][0]['spend']
   - Each step can fail - check at every level
   - Better to say "Data unavailable" than invent numbers
   - When formatting, extract values DIRECTLY from source
   - NEVER approximate, estimate, or round unless you have the exact source value

🚨 ERROR RECOGNITION PATTERN:
   - ALWAYS check responses for 'error' field
   - If 'error' exists, the operation FAILED
   - Failed operations produce NO valid data
   - You CANNOT use data from failed operations
   - Error in step 1 means steps 2, 3, etc. may fail too
   - Think: "Did this actually work or did it fail?"
   - If it failed, SAY it failed - don't pretend success

🔗 DEPENDENCY THINKING:
   - Operations depend on previous results
   - If Step 1 fails to get campaign ID, Step 2 CANNOT update it
   - Think: "What data does this step need?"
   - Think: "Did the previous step provide that data?"
   - If previous step failed, this step will likely fail
   - Don't proceed with operations that depend on failed steps
   - Example: Can't update budget without finding the adset first

❌ UNDERSTANDING ERRORS & RECOVERY:
   - "Field X specified more than once" = you passed wrong parameter format
     → Usually means you passed a string instead of a list
   - "Invalid field" = field name doesn't exist
     → Check available fields or omit the parameter
   - Empty results = no data for that time period
     → Try different date_preset or explain no activity
   - "object has no attribute" = method doesn't exist or bug
     → Try alternative approach: parent->children pattern
   - When search fails, think of hierarchical alternatives:
     → Can't search adsets? Get campaign first, then its adsets
     → Can't find by name? Get all and filter
   - Learn from errors and adjust your approach

✅ OPERATION VERIFICATION PATTERNS:
   - After any update operation, check the response
   - Look for success=True or error fields
   - Don't assume success - verify it
   - If operation claims success but no data changes, investigate
   - For budget updates: response['success'] must be True
   - Only tell user "updated successfully" if verified
   - If unsure, say "Update requested" not "Update completed"

⚡ FAILURE REPORTING PRINCIPLES:
   - Be HONEST about what happened
   - "I encountered an error" is better than fake success
   - If Step 1 fails, report: "Unable to find campaign due to API error"
   - Don't make up data to fill gaps from failures
   - Users appreciate honesty about problems
   - Explain what went wrong if you can identify it
   - Suggest solutions or alternatives when possible

META ADS HIERARCHY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Account → Campaigns → Ad Sets (cities/audiences) → Ads

Navigate this hierarchy to get detailed data!

PLANNING YOUR RESPONSE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Think through the problem step by step:
1. What data does the user want?
2. Which methods can provide that data?
3. Do I need multiple steps to get all the data?
4. What parameters should I use?

Return your plan as JSON:

For multi-step operations:
{
    "reasoning": "explain your thinking process and data flow",
    "intent": "what you understood the user wants",
    "operations": [
        {"sdk_method": "method1", "parameters": {"param": "value"}},
        {"sdk_method": "method2", "parameters": {"id": "result_from_0"}, "uses_result_from": 0},
        {"sdk_method": "method3", "parameters": {"date_preset": "last_7d"}, "iterate_on": "result_from_1"}
    ]
}

Use "iterate_on": "result_from_X" when you need to run an operation for EACH item in a list result.

When you need data for multiple items:
Think: Do I need the same operation for each item?
If yes, use "iterate_on" to express this:

Example - Getting metrics for each city:
{
    "reasoning": "User wants metrics BY city. No time specified, so use maximum data. Need insights for EACH adset",
    "intent": "Get spend and ROAS for each city individually",
    "operations": [
        {"sdk_method": "search_campaigns", "parameters": {"query": "name"}},
        {"sdk_method": "get_adsets_for_campaign", "parameters": {"campaign_id": "result_from_0"}, "uses_result_from": 0},
        {"sdk_method": "get_adset_insights", "parameters": {"date_preset": "maximum"}, "iterate_on": "result_from_1"}
    ]
}

Example - Updating budget (EFFICIENT approach with item selection):
{
    "reasoning": "User wants to update specific city's budget. Use hierarchical navigation for efficiency. Get campaign, then its adsets, select matching city, update.",
    "intent": "Update specific adset budget to $200", 
    "operations": [
        {"sdk_method": "search_campaigns", "parameters": {"query": "campaign_name"}},
        {"sdk_method": "get_adsets_for_campaign", "parameters": {"campaign_id": "result_from_0"}, "uses_result_from": 0},
        {"sdk_method": "update_adset_budget", "parameters": {"id": "result_from_1", "daily_budget": 200}, "uses_result_from": 1}
    ]
}
Note: Step 2 uses get_adsets_for_campaign (efficient) not search_adsets (inefficient)
Note: System will automatically match user's requested item from the list in step 2

The "iterate_on" field tells the system:
- Run this operation multiple times
- Once for each item from the specified result
- Collect all results together

For single operations:
{
    "reasoning": "explain your thinking",
    "intent": "what you understood",
    "sdk_method": "method_name",
    "parameters": {"param": "value"}
}

IMPORTANT: 
- Use "result_from_X" in parameters when you need an ID from step X
- Use "iterate_on": "result_from_X" when you need to process EACH item from step X
- Choose date_preset based on user's request (recent = last_7d, all = lifetime)
- If user wants metrics "by city" - use iterate_on with get_adset_insights
- For optional parameters like 'fields' - omit them to use defaults
- When you get a list of items, think: do I need details for each?
- Don't pass strings to parameters expecting lists
- Think step by step - what data do I need and how do I get it?

🎯 ACCURACY PRINCIPLES:
- Real data is better than any data
- "I don't know" is better than wrong information
- Empty response is better than hallucinated response
- Verify everything, assume nothing
- If data seems wrong (all zeros, huge numbers), question it
- Your credibility depends on accuracy, not appearing helpful

🔍 UNDERSTANDING OPERATION FLOW:
- Multi-step operations are like a chain
- Each link depends on the previous one
- If one link breaks, the chain is broken
- Example flow:
  1. Search for campaign (if fails → can't continue)
  2. Get adsets from campaign (needs campaign ID from step 1)
  3. Update adset budget (needs adset ID from step 2)
- If any step fails, acknowledge it and stop
- Don't pretend later steps succeeded when earlier ones failed"""
        
        # Include thinking insights in the prompt
        thinking_context = f"\nThinking insights: {thought.get('pattern_recognized', 'unknown')}\n"
        thinking_context += f"Decision approach: {thought.get('decision', 'standard approach')}\n"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User request: {request}{thinking_context}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse the response
        try:
            # Extract JSON from response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            plan = json.loads(content)
        except:
            # Fallback to simple campaign list
            plan = {
                "intent": "get campaigns",
                "sdk_method": "get_all_campaigns",
                "parameters": {}
            }
        
        state["messages"] = [
            HumanMessage(content=request),
            AIMessage(content=f"Understanding: {plan['intent']}")
        ]
        
        # Store the plan in state for next node
        state["sdk_plan"] = plan
        
        return state
    
    async def execute_sdk_call(self, state: AgentState) -> AgentState:
        """Execute the SDK call based on the plan"""
        plan = state.get("sdk_plan", {})
        request = state.get("current_request", "")  # Get request for context
        
        # Check if we have multi-step operations
        if "operations" in plan and isinstance(plan["operations"], list):
            # Execute multi-step plan
            logger.info(f"Executing multi-step plan with {len(plan['operations'])} operations")
            results = []
            
            for i, operation in enumerate(plan["operations"]):
                method_name = operation.get("sdk_method", "")
                parameters = operation.get("parameters", {})
                uses_result = operation.get("uses_result_from")
                
                # Check if previous step failed and this step depends on it
                if uses_result is not None and uses_result < len(results):
                    prev_result = results[uses_result]
                    if isinstance(prev_result, dict) and "error" in prev_result:
                        logger.error(f"Step {i+1} skipped: Step {uses_result+1} failed with error")
                        results.append({
                            "error": f"Cannot proceed: Step {uses_result+1} failed",
                            "dependency_failure": True,
                            "failed_step": uses_result + 1
                        })
                        continue
                
                # Check if this operation should iterate over results
                iterate_on = operation.get("iterate_on")
                if iterate_on and isinstance(iterate_on, str) and iterate_on.startswith("result_from_"):
                    # Extract the result index to iterate on
                    try:
                        iterate_index = int(iterate_on.split("_")[-1])
                        if iterate_index < len(results):
                            items_to_iterate = results[iterate_index]
                            if isinstance(items_to_iterate, list):
                                # Execute this operation for each item
                                iteration_results = []
                                for item in items_to_iterate:
                                    item_id = item.get("id") if isinstance(item, dict) else None
                                    if item_id:
                                        # Create parameters for this iteration
                                        iter_params = parameters.copy()
                                        # Add the ID parameter - try to be smart about parameter name
                                        # Check method signature to determine correct parameter name
                                        try:
                                            method = getattr(self.sdk, method_name, None)
                                            if method and callable(method):
                                                sig = inspect.signature(method)
                                                param_names = list(sig.parameters.keys())
                                                # Try to find the right parameter name
                                                if "adset_id" in param_names:
                                                    iter_params["adset_id"] = item_id
                                                elif "id" in param_names:
                                                    iter_params["id"] = item_id
                                                elif "campaign_id" in param_names:
                                                    iter_params["campaign_id"] = item_id
                                                else:
                                                    # Default to 'id' if we can't determine
                                                    iter_params["id"] = item_id
                                        except:
                                            # Fallback to 'id' if inspection fails
                                            iter_params["id"] = item_id
                                        
                                        logger.info(f"Iterating {method_name} for item {item.get('name', item_id)}")
                                        try:
                                            method = getattr(self.sdk, method_name, None)
                                            if method:
                                                iter_result = method(**iter_params)
                                                # Add context about which item this is for
                                                if isinstance(iter_result, dict):
                                                    iter_result["_for_item"] = {"id": item_id, "name": item.get("name", "")}
                                                    # Log the actual data we got
                                                    if "spend" in iter_result or "spend_dollars" in iter_result:
                                                        spend = iter_result.get("spend_dollars", iter_result.get("spend", 0))
                                                        logger.info(f"  → Got spend for {item.get('name', 'Unknown')}: ${spend}")
                                                iteration_results.append(iter_result)
                                        except Exception as e:
                                            logger.error(f"Error in iteration for {item_id}: {e}")
                                            iteration_results.append({"error": str(e), "_for_item": {"id": item_id}})
                                
                                results.append(iteration_results)
                                continue  # Skip normal execution since we iterated
                    except (ValueError, IndexError):
                        logger.error(f"Invalid iterate_on value: {iterate_on}")
                
                # Normal execution (non-iteration) with result substitution
                if uses_result is not None and uses_result < len(results):
                    prev_result = results[uses_result]
                    # Extract ID from previous result and substitute placeholders
                    result_id = None
                    if isinstance(prev_result, list) and len(prev_result) > 0:
                        # Apply thinking pattern: Find specific item mentioned in request
                        request = state.get("current_request", "")
                        
                        # Pattern: When user mentions a specific item and we have a list
                        # THINK: How to match user intent to available items?
                        if "update" in method_name.lower() and prev_result:
                            # Think about item selection
                            selection_context = f"Need to select item from list. Request: {request}. Available items: {[item.get('name', '') for item in prev_result if isinstance(item, dict)]}"
                            selection_thought = await self.think(selection_context)
                            logger.info(f"Selection thinking: {selection_thought.get('decision')}")
                            
                            # Extract location/city names from request using pattern matching
                            words = request.split()
                            
                            # Try to find matching item by name
                            matched_item = None
                            for item in prev_result:
                                item_name = item.get("name", "").lower()
                                # Check each word in request against item names
                                for word in words:
                                    if len(word) > 2 and word[0].isupper():  # Likely a proper noun
                                        if word.lower() in item_name:
                                            matched_item = item
                                            logger.info(f"Found matching item: {item.get('name')} for request keyword: {word}")
                                            break
                                if matched_item:
                                    break
                            
                            if matched_item:
                                result_id = matched_item.get("id")
                            else:
                                # No specific match found, use first item
                                logger.info("No specific item match found, using first item")
                                result_id = prev_result[0].get("id")
                        else:
                            result_id = prev_result[0].get("id")
                    elif isinstance(prev_result, dict):
                        result_id = prev_result.get("id")
                        # Check if previous step had an error
                        if prev_result.get("error"):
                            logger.error(f"Skipping {method_name} due to previous error: {prev_result['error']}")
                            results.append({
                                "error": f"Cannot execute {method_name}: Previous step failed",
                                "previous_error": prev_result['error'],
                                "skipped": True
                            })
                            continue
                    
                    # Replace placeholder values with actual IDs
                    if result_id:
                        for param_key, param_value in list(parameters.items()):
                            # If parameter value is a placeholder like "result_from_0", replace it
                            if isinstance(param_value, str) and param_value.startswith("result_from_"):
                                parameters[param_key] = result_id
                                logger.info(f"Replaced {param_key}={param_value} with actual ID: {result_id}")
                
                # Clean method name
                if method_name.startswith("sdk."):
                    method_name = method_name[4:]
                
                # Skip if we already handled this as an iteration
                if iterate_on and iterate_on.startswith("result_from_"):
                    continue
                    
                logger.info(f"Step {i+1}: {method_name} with params: {parameters}")
                
                # Execute this step
                try:
                    method = getattr(self.sdk, method_name, None)
                    if not method:
                        result = self.sdk.query(method_name, parameters)
                    else:
                        if parameters:
                            result = method(**parameters)
                        else:
                            result = method()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in step {i+1}: {e}")
                    error_result = {"error": str(e), "step_failed": i+1}
                    results.append(error_result)
                    
                    # If this is a critical early step, mark that subsequent steps may fail
                    if i == 0:  # First step is usually critical (finding the campaign/adset)
                        logger.error(f"Critical first step failed - subsequent steps may not work")
            
            # Check if any critical errors occurred
            has_errors = any(isinstance(r, dict) and "error" in r for r in results)
            
            # THINK: Verify the results and learn from the outcome
            verification_context = f"Operations completed. Has errors: {has_errors}. Results summary: {len(results)} operations executed."
            if has_errors:
                verification_context += f" Errors found in results."
            verification_thought = await self.think(verification_context)
            logger.info(f"Verification thinking: {verification_thought.get('verification_approach')}")
            
            # Combine all results
            state["sdk_response"] = {
                "multi_step_results": results,
                "operations": plan["operations"],
                "has_errors": has_errors,
                "verification_thought": verification_thought
            }
            
            if has_errors:
                error_count = sum(1 for r in results if isinstance(r, dict) and "error" in r)
                state["messages"].append(
                    AIMessage(content=f"Executed {len(results)} operations with {error_count} errors")
                )
            else:
                state["messages"].append(
                    AIMessage(content=f"Executed {len(results)} operations successfully")
                )
            return state
        
        # Single operation (backward compatibility)
        method_name = plan.get("sdk_method", "get_all_campaigns")
        parameters = plan.get("parameters", {})
        reasoning = plan.get("reasoning", "")
        
        # Clean method name (remove 'sdk.' prefix if present)
        if method_name.startswith("sdk."):
            method_name = method_name[4:]
        
        logger.info(f"Executing SDK method: {method_name} with params: {parameters}")
        logger.info(f"Reasoning: {reasoning}")
        
        try:
            # Get the SDK method
            method = getattr(self.sdk, method_name, None)
            if not method:
                # Try direct query if method doesn't exist
                result = self.sdk.query(method_name, parameters)
            else:
                # Call the method with parameters if provided
                if parameters:
                    result = method(**parameters)
                else:
                    result = method()
            
            state["sdk_response"] = result
            state["messages"].append(
                AIMessage(content=f"Retrieved data successfully")
            )
        except Exception as e:
            logger.error(f"SDK error: {e}")
            state["sdk_response"] = {"error": str(e)}
            state["messages"].append(
                AIMessage(content=f"Error retrieving data: {str(e)}")
            )
        
        return state
    
    async def format_response(self, state: AgentState) -> AgentState:
        """Format the SDK response for Discord using AUTONOMOUS PATTERN RECOGNITION"""
        sdk_response = state.get("sdk_response", {})
        request = state["current_request"]
        
        # AUTONOMOUS THINKING: Analyze what type of operation was performed
        # No hardcoded field checks - recognize patterns instead
        
        # First, think about what patterns we see
        operation_pattern = await self.recognize_operation_pattern(sdk_response)
        logger.info(f"Recognized operation pattern: {operation_pattern}")
        
        # Check for errors FIRST
        if isinstance(sdk_response, dict):
            # Check if there are errors in the response
            if "error" in sdk_response:
                logger.error(f"SDK returned error: {sdk_response['error']}")
                state["final_answer"] = f"❌ Error: {sdk_response['error'][:200]}\n\nI was unable to complete your request."
                state["messages"].append(AIMessage(content=state["final_answer"]))
                return state
            
            # Check for errors in multi-step operations
            if "has_errors" in sdk_response and sdk_response["has_errors"]:
                logger.warning("Multi-step operation had errors")
        
        # Check if this was a multi-step operation
        if "multi_step_results" in sdk_response:
            # Format multi-step results using PATTERN RECOGNITION
            results = sdk_response["multi_step_results"]
            operations = sdk_response["operations"]
            
            # Build a view of the data WITHOUT hardcoded field names
            formatted_data = {
                "request": request,
                "steps_executed": len(operations),
                "operation_pattern": operation_pattern,
                "results": {}
            }
            
            for i, (op, result) in enumerate(zip(operations, results)):
                step_name = op.get("sdk_method", "unknown")
                
                # PATTERN RECOGNITION: Identify data structures by their patterns
                if op.get("iterate_on") and isinstance(result, list):
                    # Pattern: Array of results from iteration
                    formatted_data["results"][f"step_{i+1}_results"] = result
                    # If these look like metrics (have numeric fields), process them
                    if result and isinstance(result[0], dict) and any(isinstance(v, (int, float)) for v in result[0].values()):
                        formatted_data["results"]["data_items"] = []
                        for item_result in result:
                            if isinstance(item_result, dict):
                                # PATTERN: Extract data based on structure, not field names
                                item_data = {}
                                
                                # Look for name-like fields (patterns, not hardcoded)
                                for key, value in item_result.items():
                                    if "name" in key.lower() or key == "_for_item":
                                        if isinstance(value, dict) and "name" in value:
                                            item_data["identifier"] = value["name"]
                                        elif isinstance(value, str):
                                            item_data["identifier"] = value
                                
                                # Look for numeric metrics (patterns, not specific fields)
                                for key, value in item_result.items():
                                    if isinstance(value, (int, float)):
                                        item_data[key] = value
                                    elif isinstance(value, list) and value and isinstance(value[0], dict):
                                        # Pattern: Array of metric objects
                                        if "value" in value[0]:
                                            item_data[key] = float(value[0].get("value", 0))
                                
                                if item_data:
                                    formatted_data["results"]["data_items"].append(item_data)
                        
                        # Log what we found using patterns
                        logger.info(f"Found {len(formatted_data['results'].get('data_items', []))} data items through pattern recognition")
                elif isinstance(result, list) and len(result) > 0:
                    # Pattern: List of results
                    formatted_data["results"][f"step_{i+1}_results"] = result
                elif isinstance(result, dict):
                    # Pattern: Single result object
                    formatted_data["results"][f"step_{i+1}_result"] = result
                else:
                    # Store whatever we got
                    formatted_data["results"][f"step_{i+1}_output"] = result
            
            sdk_response = formatted_data
            # Log what patterns we recognized
            logger.info(f"✅ Processed response using {operation_pattern} pattern recognition")
        
        # BUILD DYNAMIC PROMPT based on recognized pattern - NO HARDCODED FIELDS
        if operation_pattern == "UPDATE":
            system_prompt = """You are formatting an UPDATE operation response for Discord. 

🔴 ERROR HANDLING FIRST 🔴
BEFORE formatting any data, check:
1. Is there an 'error' field in the data?
2. Are there 'has_errors' or failed operations?
3. If yes, REPORT THE ERROR, don't make up success

If you see errors:
- Report what failed and why
- Don't claim operations succeeded
- Don't make up fake data to fill gaps
- Be honest: "Unable to update budget due to API error"

🚨 CRITICAL DATA EXTRACTION PROCESS 🚨

You MUST follow these steps EXACTLY:

STEP 1: Check for errors AND successes
  - Look for 'error' fields in the data
  - Look for 'has_errors' flag
  - ALSO look for 'success': true in update operations
  - If you see success=true, report SUCCESS not error
  - Only report error if there's an actual error field

STEP 2: Locate the data
  - Look for 'city_metrics' in the provided JSON
  - It should be an array of city objects
  - If not found, respond: "Unable to retrieve metrics data"

STEP 3: Extract values for each city
  - For each city object in city_metrics:
    - City name: city['city'] 
    - Spend: city['spend'] (use EXACTLY as provided)
    - ROAS: city['roas'] (use EXACTLY as provided)
  - If a field is missing, write "N/A" not a number

STEP 4: Validation
  - ONLY use numbers that appear in the source data
  - NEVER generate, estimate, or round numbers
  - If you can't find a value, DO NOT make one up
  - Better to show "Data unavailable" than fake numbers

STEP 5: Format the output
  - Use the EXACT values from city_metrics
  - NEVER round or modify values
  - If spend is 388.08, write $388.08, NOT $388
  - If spend is 52.91, write $52.91, NOT $53
  - Always include 2 decimal places for spend values
  - Copy numbers EXACTLY as they appear in the data

⚠️ CRITICAL: USE EXACT NUMBERS FROM city_metrics - NO ROUNDING OR ESTIMATES ⚠️

🛑 HALLUCINATION CHECK:
Before outputting ANY number, ask yourself:
  - Did I extract this EXACT value from city_metrics?
  - Am I copying it precisely without modification?
  - If not, STOP and write "N/A" instead

⚠️ OPERATION SUCCESS CHECK:
  - NEVER claim "successfully updated" unless you see success=True
  - If operation failed, say "Unable to update due to error"
  - Don't make up confirmation messages for failed operations
  - IMPORTANT: If you see success=True in step_3_update_adset_budget, the update WORKED
  - Look for: {"success": true, "message": "Successfully updated..."}
  - If this exists, report SUCCESS not error!

FORMATTING RULES:
1. Clean up city names:
   - "Sende Tour - LA" → "**Los Angeles**" 
   - "Sende Tour - Brooklyn" → "**Brooklyn**"
   - "Sende Tour - Miami" → "**Miami**"
   - "Sende Tour - Houston" → "**Houston**"
   - "Sende Tour - Chicago" → "**Chicago**"
   - "Sende Tour - Retargeting - exclude sales" → "**Retargeting**"

2. For spend and ROAS values:
   - Use EXACT numbers from city_metrics - NO ROUNDING
   - Always show exact value with 2 decimals: $388.08, $52.91
   - NEVER round to whole dollars
   - Copy the exact 'spend' value from city_metrics
   - Format ROAS with exact decimals from source
   - If ROAS > 20, add 💪 emoji
   - Values are already in dollars, no conversion needed

3. Present as a clean list or compact format:
   📍 **City** → Spend: $X.XX | ROAS: X.Xx
   
4. Add summary at bottom:
   - Total spend: Calculate the ACTUAL sum from city_metrics data
   - Best performing city (highest ROAS from city_metrics)
   - IMPORTANT: Sum the exact values, don't estimate

5. Use emojis sparingly for visual appeal:
   - 🎯 for campaign name
   - 📍 for cities
   - 💰 for totals
   - 🏆 for best performer

Keep response under 1500 chars. Be concise and professional."""
        
        elif operation_pattern == "QUERY":
            system_prompt = """You are formatting a QUERY operation response for Discord.

🔍 AUTONOMOUS PATTERN RECOGNITION:
1. Look for DATA patterns:
   - Arrays of similar objects (list of items)
   - Objects with numeric values (metrics)
   - Objects with text values (names, identifiers)
   
2. Identify the data structure:
   - Is it a list of items? Format as a list
   - Is it metrics data? Show the numbers
   - Is it a single item? Show its details
   
3. Extract values based on PATTERNS:
   - Look for name-like fields (containing 'name', 'title', 'label')
   - Look for numeric fields (numbers, decimals)
   - Look for identifier fields (containing 'id', 'key')

📝 FORMAT:
Present the data cleanly based on what you find:
- For lists: Show each item
- For metrics: Show the values
- Use exact numbers, no rounding
- Add emojis sparingly for visual appeal

DO NOT look for specific field names like 'city_metrics'.
Recognize and format whatever data patterns you find.

Keep response under 1500 chars. Be concise and professional."""
        
        else:
            system_prompt = """You are formatting a response for Discord.

🔍 AUTONOMOUS ANALYSIS:
1. Analyze the response structure
2. Identify what type of data this is
3. Format appropriately based on patterns

Look for patterns, not specific field names:
- Arrays = lists of items
- Objects with 'success'/'error' = operation results  
- Objects with numbers = metrics

Present the information clearly and concisely.
Keep response under 1500 chars. Be concise and professional."""
        
        # Log the data we're about to format - NO HARDCODED FIELD CHECKS
        logger.info(f"Formatting {operation_pattern} response with data keys: {sdk_response.keys() if isinstance(sdk_response, dict) else type(sdk_response)}")
        
        # Prepare data for LLM - send the full response without looking for specific fields
        data_str = json.dumps(sdk_response, indent=2)
        if len(data_str) > 8000:
            data_str = data_str[:8000]
            logger.info("Response truncated to 8000 chars")
        
        # Log what patterns we're sending
        logger.info(f"Sending to LLM - Data length: {len(data_str)} chars")
        logger.info(f"Using {operation_pattern} pattern formatting")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User asked: {request}"),
            HumanMessage(content=f"Data retrieved: {data_str}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Post-validation: Pattern-based validation (no hardcoded fields)
        final_answer = response.content
        
        # Validate based on operation pattern
        if operation_pattern == "UPDATE":
            # For UPDATE operations, check if response mentions success/failure
            if "success" not in final_answer.lower() and "error" not in final_answer.lower() and "update" not in final_answer.lower():
                logger.warning("⚠️ UPDATE response may be missing status indication")
        elif operation_pattern == "QUERY":
            # For QUERY operations, check if response has data
            import re
            # Check for numeric values in response
            response_amounts = re.findall(r'\$([\d,]+\.?\d*)', final_answer)
            if len(response_amounts) == 0 and "no data" not in final_answer.lower() and "unable" not in final_answer.lower():
                logger.warning("⚠️ QUERY response may be missing data")
        
        state["final_answer"] = final_answer
        state["messages"].append(AIMessage(content=final_answer))
        
        return state
    
    async def process_request(self, request: str) -> str:
        """Process a user request and return formatted response"""
        # Initialize state
        initial_state = {
            "messages": [],
            "current_request": request,
            "sdk_response": None,
            "final_answer": "",
            "sdk_plan": {}  # Initialize the sdk_plan field
        }
        
        # Run the graph with LangSmith tracing
        try:
            # Use tracing context for LangSmith
            project_name = os.getenv("LANGCHAIN_PROJECT", "OutletMediaBot")
            with tracing_v2_enabled(project_name=project_name):
                result = await self.graph.ainvoke(initial_state)
                logger.info(f"LangSmith trace created for project: {project_name}")
            return result.get("final_answer", "I couldn't process your request.")
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return f"❌ Error: {str(e)[:500]}"


# Create tools for the agent to use
@tool
def get_campaigns_tool(status: str = "all") -> Dict:
    """Get campaigns by status (all, active, paused)"""
    sdk = MetaAdsSDK()
    if status == "active":
        return sdk.get_campaigns_by_status(["ACTIVE"])
    elif status == "paused":
        return sdk.get_campaigns_by_status(["PAUSED"])
    else:
        return sdk.get_all_campaigns()


@tool
def get_campaign_performance(campaign_id: str = None, date_preset: str = "today") -> Dict:
    """Get performance metrics for campaigns"""
    sdk = MetaAdsSDK()
    if campaign_id:
        return sdk.get_campaign_insights(campaign_id, date_preset)
    else:
        return sdk.get_performance_metrics(date_preset)


@tool
def search_campaigns(query: str) -> Dict:
    """Search for campaigns by name or ID"""
    sdk = MetaAdsSDK()
    return sdk.search_campaigns(query)