#!/usr/bin/env python3
"""
Run Meta Ads Bot locally (without Discord connection)
Useful for testing and debugging with LangSmith
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
project_name = os.getenv("LANGCHAIN_PROJECT", "MetaAdsBot-Local")
os.environ["LANGCHAIN_PROJECT"] = project_name

print("🤖 Meta Ads Bot - Local Testing Mode")
print("=" * 50)
print(f"📊 LangSmith Project: {project_name}")
print(f"🔗 Traces: https://smith.langchain.com")
print("=" * 50)

async def interactive_mode():
    """Run bot in interactive mode"""
    from agents.meta_ads_agent import MetaAdsAgent
    
    print("\n✅ Bot initialized! Type your questions (or 'quit' to exit)\n")
    
    agent = MetaAdsAgent()
    
    while True:
        try:
            # Get user input
            query = input("\n💬 You: ").strip()
            
            if query.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            if not query:
                continue
            
            # Process with agent
            print("🤔 Thinking...")
            response = await agent.process_request(query)
            
            # Print response
            print("\n🤖 Bot:", response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Error processing query: {e}", exc_info=True)

async def batch_test_mode():
    """Run predefined tests"""
    from agents.meta_ads_agent import MetaAdsAgent
    
    agent = MetaAdsAgent()
    
    test_queries = [
        "How many active campaigns?",
        "What's my total spend today?",
        "Show me the best performing campaign",
        "Which campaigns are paused?",
        "What's the average CTR?",
    ]
    
    print("\n📝 Running batch tests...")
    print("-" * 40)
    
    for query in test_queries:
        print(f"\n💬 Query: {query}")
        try:
            response = await agent.process_request(query)
            print(f"✅ Response: {response[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await asyncio.sleep(1)  # Small delay
    
    print("\n✅ Batch tests complete!")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Meta Ads Bot locally')
    parser.add_argument(
        '--mode', 
        choices=['interactive', 'batch'], 
        default='interactive',
        help='Run mode: interactive or batch testing'
    )
    
    args = parser.parse_args()
    
    # Check environment
    required = ['META_ACCESS_TOKEN', 'META_AD_ACCOUNT_ID', 'OPENAI_API_KEY']
    missing = [v for v in required if not os.getenv(v)]
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        print("Please check your .env file")
        sys.exit(1)
    
    # Run appropriate mode
    if args.mode == 'interactive':
        print("\n🎮 Starting interactive mode...")
        asyncio.run(interactive_mode())
    else:
        print("\n🧪 Starting batch test mode...")
        asyncio.run(batch_test_mode())

if __name__ == "__main__":
    main()