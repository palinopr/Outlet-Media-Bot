#!/usr/bin/env python3
"""
Test Meta Ads Bot locally with LangSmith tracing
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

# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = f"MetaAdsBot-Test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

print("🧪 Testing Meta Ads Bot with LangSmith Tracing")
print("=" * 50)
print(f"📊 LangSmith Project: {os.environ['LANGCHAIN_PROJECT']}")
print(f"🔗 View traces at: https://smith.langchain.com")
print("=" * 50)

async def test_agent():
    """Test the Meta Ads agent directly"""
    try:
        # Import agent
        from agents.meta_ads_agent import MetaAdsAgent
        
        print("\n✅ Agent imported successfully")
        
        # Initialize agent
        agent = MetaAdsAgent()
        print("✅ Agent initialized")
        
        # Test queries
        test_queries = [
            "How many campaigns do I have?",
            "Show me active campaigns",
            "What's my spend today?",
            "Show campaign performance",
        ]
        
        print("\n📝 Testing queries:")
        print("-" * 40)
        
        for query in test_queries:
            print(f"\n💬 Query: {query}")
            print("Processing...")
            
            try:
                # Process request
                response = await agent.process_request(query)
                
                # Show response (truncated)
                print(f"✅ Response received ({len(response)} chars)")
                print(f"Preview: {response[:200]}...")
                
                # Small delay between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print(f"\n🔍 View detailed traces in LangSmith:")
        print(f"   https://smith.langchain.com/o/*/projects/p/{os.environ['LANGCHAIN_PROJECT']}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're in the correct directory and dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_sdk_direct():
    """Test Meta SDK directly"""
    print("\n📱 Testing Meta SDK directly:")
    print("-" * 40)
    
    try:
        from tools.meta_sdk import MetaAdsSDK
        
        sdk = MetaAdsSDK()
        print("✅ SDK initialized")
        
        # Test basic query
        print("Getting all campaigns...")
        campaigns = sdk.get_all_campaigns()
        
        if isinstance(campaigns, dict) and "error" in campaigns:
            print(f"⚠️  API Error: {campaigns['error']}")
        elif isinstance(campaigns, list):
            print(f"✅ Found {len(campaigns)} campaigns")
            for camp in campaigns[:3]:  # Show first 3
                print(f"   - {camp.get('name', 'Unknown')} ({camp.get('status', 'Unknown')})")
        else:
            print("✅ SDK call successful")
            
    except Exception as e:
        print(f"❌ SDK Error: {e}")

async def test_full_stack():
    """Test the full Discord bot stack"""
    print("\n🤖 Testing Full Bot Stack:")
    print("-" * 40)
    
    try:
        from agents.discord_bot import MetaAdsDiscordBot
        
        # Just test initialization, don't actually connect to Discord
        print("Initializing Discord bot (without connecting)...")
        
        # We'll mock the token temporarily
        if not os.getenv("DISCORD_BOT_TOKEN"):
            os.environ["DISCORD_BOT_TOKEN"] = "test_token_for_init"
            bot = MetaAdsDiscordBot()
            del os.environ["DISCORD_BOT_TOKEN"]
        else:
            bot = MetaAdsDiscordBot()
        
        print("✅ Discord bot initialized (not connected)")
        print("✅ Agent is ready")
        
        # Test agent directly through bot
        test_message = "How many active campaigns?"
        print(f"\n🧪 Simulating message: '{test_message}'")
        response = await bot.agent.process_request(test_message)
        print(f"✅ Got response: {response[:100]}...")
        
    except Exception as e:
        print(f"⚠️  Bot initialization: {e}")
        print("This is expected if DISCORD_BOT_TOKEN is not set")

def main():
    """Run all tests"""
    print("\n🚀 Starting comprehensive local test with LangSmith tracing\n")
    
    # Check environment
    required_vars = {
        'META_ACCESS_TOKEN': '✅' if os.getenv('META_ACCESS_TOKEN') else '❌',
        'META_AD_ACCOUNT_ID': '✅' if os.getenv('META_AD_ACCOUNT_ID') else '❌',
        'OPENAI_API_KEY': '✅' if os.getenv('OPENAI_API_KEY') else '❌',
        'LANGCHAIN_API_KEY': '✅' if os.getenv('LANGCHAIN_API_KEY') else '❌',
        'DISCORD_BOT_TOKEN': '✅' if os.getenv('DISCORD_BOT_TOKEN') else '⚠️ (optional)',
    }
    
    print("Environment Check:")
    for var, status in required_vars.items():
        print(f"  {status} {var}")
    
    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run tests
        loop.run_until_complete(test_sdk_direct())
        loop.run_until_complete(test_agent())
        loop.run_until_complete(test_full_stack())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()
    
    print("\n" + "=" * 50)
    print("🏁 Testing complete!")
    print("\n📊 Check your traces in LangSmith:")
    print(f"   Project: {os.getenv('LANGCHAIN_PROJECT')}")
    print("   URL: https://smith.langchain.com")

if __name__ == "__main__":
    main()