"""
Meta Ads Agent using LangGraph v2.0.1
Simple agent that can think about requests and use Meta SDK tools
Enhanced with multi-step planning and autonomous operation chaining
"""
import os
import logging
import json
from typing import Dict, Any, List, TypedDict, Annotated
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
        
        # Create the graph
        self.graph = self._create_graph()
    
    def _create_graph(self):
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("understand_request", self.understand_request)
        workflow.add_node("execute_sdk_call", self.execute_sdk_call)
        workflow.add_node("format_response", self.format_response)
        
        # Add edges
        workflow.set_entry_point("understand_request")
        workflow.add_edge("understand_request", "execute_sdk_call")
        workflow.add_edge("execute_sdk_call", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def understand_request(self, state: AgentState) -> AgentState:
        """Understand what the user is asking for"""
        request = state["current_request"]
        
        # Use LLM to understand the request and plan SDK call
        # Get available SDK methods dynamically
        sdk_methods = [method for method in dir(self.sdk) if not method.startswith('_')]
        
        # Get actual method signatures dynamically using introspection
        import inspect
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
🔍 DISCOVERY PATTERN:
   - Look at method names to understand their purpose
   - Methods starting with 'search_' find specific items
   - Methods starting with 'get_' retrieve data
   - Methods with 'insights' return metrics (spend, ROAS, clicks)
   - Methods with 'adset' work with cities/locations

🎯 UNDERSTANDING USER INTENT:
   - "cities" = adsets in Meta Ads
   - "spend/ROAS/performance" = insights data
   - "active/paused" = status filtering
   - When user asks for specific names, use search methods
   - When user asks for metrics, use insights methods

📊 INSIGHTS PATTERN:
   - Insights methods accept date_preset parameter
   - Common values: "today", "yesterday", "last_7d", "last_30d", "lifetime"
   - If user asks for recent data, use "last_7d" by default
   - If user asks for all-time data, use "lifetime"
   - For city-level metrics, use get_adset_insights if available

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

💡 WHEN USER ASKS FOR METRICS BY CITY:
   - Cities are adsets
   - Look for methods with 'adset' and 'insights'
   - get_adset_insights can get metrics per city
   - Plan: search campaign → get adsets → get insights for each

🔄 HANDLING EMPTY RESULTS:
   - If insights return empty, try different date_preset
   - Start with "last_7d" for recent data
   - Try "lifetime" for all-time data
   - Explain to user what you tried

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
    "reasoning": "explain your thinking process",
    "intent": "what you understood the user wants",
    "operations": [
        {"sdk_method": "method1", "parameters": {"param": "value"}},
        {"sdk_method": "method2", "parameters": {"id": "result_from_0"}, "uses_result_from": 0}
    ]
}

For single operations:
{
    "reasoning": "explain your thinking",
    "intent": "what you understood",
    "sdk_method": "method_name",
    "parameters": {"param": "value"}
}

IMPORTANT: 
- Use "result_from_X" when you need an ID from step X
- Choose date_preset based on user's request (recent = last_7d, all = lifetime)
- If user wants city metrics, plan to get insights for each adset
- Think autonomously - figure out the best approach!"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User request: {request}")
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
        
        # Check if we have multi-step operations
        if "operations" in plan and isinstance(plan["operations"], list):
            # Execute multi-step plan
            logger.info(f"Executing multi-step plan with {len(plan['operations'])} operations")
            results = []
            
            for i, operation in enumerate(plan["operations"]):
                method_name = operation.get("sdk_method", "")
                parameters = operation.get("parameters", {})
                uses_result = operation.get("uses_result_from")
                
                # If this operation uses results from a previous one
                if uses_result is not None and uses_result < len(results):
                    prev_result = results[uses_result]
                    # Extract ID from previous result and substitute placeholders
                    result_id = None
                    if isinstance(prev_result, list) and len(prev_result) > 0:
                        result_id = prev_result[0].get("id")
                    elif isinstance(prev_result, dict):
                        result_id = prev_result.get("id")
                    
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
                    results.append({"error": str(e)})
            
            # Combine all results
            state["sdk_response"] = {
                "multi_step_results": results,
                "operations": plan["operations"]
            }
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
        """Format the SDK response for Discord"""
        sdk_response = state.get("sdk_response", {})
        request = state["current_request"]
        
        # Check if this was a multi-step operation
        if "multi_step_results" in sdk_response:
            # Format multi-step results specially
            results = sdk_response["multi_step_results"]
            operations = sdk_response["operations"]
            
            # Build a comprehensive view of the data
            formatted_data = {
                "request": request,
                "steps_executed": len(operations),
                "results": {}
            }
            
            for i, (op, result) in enumerate(zip(operations, results)):
                step_name = op.get("sdk_method", "unknown")
                if "search" in step_name and isinstance(result, list) and len(result) > 0:
                    formatted_data["results"]["found_item"] = result[0]
                elif "adsets" in step_name:
                    formatted_data["results"]["adsets"] = result
                elif "insights" in step_name:
                    formatted_data["results"]["insights"] = result
                else:
                    formatted_data["results"][f"step_{i+1}_{step_name}"] = result
            
            sdk_response = formatted_data
        
        # Use LLM to format the response nicely
        system_prompt = """You are formatting Meta Ads data for Discord. 
Create a clear, concise response using:
- Emojis for visual appeal
- Bullet points for lists
- Bold for important numbers
- Tables if helpful (using Discord markdown)

For multi-step results:
- Combine the data logically
- If there are campaigns, adsets (cities), and insights - present them together
- Show the complete picture the user asked for

For UPDATE operations:
- Clearly confirm what was changed
- Show old vs new values if available
- Use ✅ for success, ❌ for errors
- Be extra clear about monetary values (show dollars, not cents)

Keep it under 2000 characters.
Be direct and helpful. Answer exactly what was asked."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User asked: {request}"),
            HumanMessage(content=f"Data retrieved: {json.dumps(sdk_response, indent=2)[:3000]}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        state["final_answer"] = response.content
        state["messages"].append(AIMessage(content=response.content))
        
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