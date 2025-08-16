"""
Meta Ads Agent using LangGraph
Simple agent that can think about requests and use Meta SDK tools
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
        system_prompt = """You are a Meta Ads API expert. Analyze the user's request and determine what SDK method to call.

The SDK has these methods for Meta Ads objects:

CAMPAIGNS:
- get_all_campaigns(): Returns all campaigns
- get_campaigns_by_status(status=["ACTIVE"]): Filter campaigns by status
- get_campaign_insights(campaign_id, date_preset="today"): Get metrics for specific campaign
- search_campaigns(query): Search campaigns by name

AD SETS:
- get_adsets_for_campaign(campaign_id): Get all ad sets for a campaign
- query("adsets", params): Get all ad sets

ADS:
- get_ads_for_adset(adset_id): Get all ads for an ad set
- query("ads", params): Get all ads

METRICS & INSIGHTS:
- get_performance_metrics(date_preset="today"): Get overall performance metrics
- query("insights", params): Get detailed insights

GENERIC:
- query(operation, params): For any other operation like "audiences", "creatives", etc.

Based on the user's request, return a JSON with:
{
    "intent": "what the user wants",
    "sdk_method": "method_name",
    "parameters": {...}
}

Examples:
- "show adsets" -> {"sdk_method": "query", "parameters": {"operation": "adsets"}}
- "get ads for campaign X" -> {"sdk_method": "get_adsets_for_campaign", "parameters": {"campaign_id": "X"}}
- "show audiences" -> {"sdk_method": "query", "parameters": {"operation": "audiences"}}"""
        
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
        method_name = plan.get("sdk_method", "get_all_campaigns")
        parameters = plan.get("parameters", {})
        
        # Clean method name (remove 'sdk.' prefix if present)
        if method_name.startswith("sdk."):
            method_name = method_name[4:]
        
        logger.info(f"Executing SDK method: {method_name} with params: {parameters}")
        
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
        
        # Use LLM to format the response nicely
        system_prompt = """You are formatting Meta Ads data for Discord. 
Create a clear, concise response using:
- Emojis for visual appeal
- Bullet points for lists
- Bold for important numbers
- Tables if helpful (using Discord markdown)

Keep it under 2000 characters.
Be direct and helpful."""
        
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