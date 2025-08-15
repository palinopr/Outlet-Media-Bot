"""
LangGraph Cloud deployment entry point
Exports the compiled graph for LangGraph Cloud/Studio
"""
import os
from dotenv import load_dotenv
from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

# Load environment
load_dotenv()

# Import our agent
from agents.meta_ads_agent import MetaAdsAgent, AgentState


def create_graph():
    """Create the LangGraph workflow for deployment"""
    
    # Initialize the agent
    agent = MetaAdsAgent()
    
    # Create workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes using the agent's methods
    workflow.add_node("understand_request", agent.understand_request)
    workflow.add_node("execute_sdk_call", agent.execute_sdk_call)
    workflow.add_node("format_response", agent.format_response)
    
    # Set entry point
    workflow.set_entry_point("understand_request")
    
    # Add edges
    workflow.add_edge("understand_request", "execute_sdk_call")
    workflow.add_edge("execute_sdk_call", "format_response")
    workflow.add_edge("format_response", END)
    
    # Compile the graph
    return workflow.compile()


# Export the compiled graph for LangGraph
graph = create_graph()


# For Discord integration (when running standalone)
async def process_discord_message(message: str) -> str:
    """Process a Discord message through the graph"""
    initial_state = {
        "messages": [],
        "current_request": message,
        "sdk_response": None,
        "final_answer": ""
    }
    
    result = await graph.ainvoke(initial_state)
    return result.get("final_answer", "I couldn't process your request.")


# For direct invocation
if __name__ == "__main__":
    import asyncio
    
    async def test():
        response = await process_discord_message("How many active campaigns do I have?")
        print(response)
    
    asyncio.run(test())