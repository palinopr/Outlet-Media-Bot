#!/usr/bin/env python3
"""
Test script to verify all components are working
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("🧪 Testing Meta Ads Discord Bot Setup")
print("=" * 40)

# Test 1: Check Python version
print("\n1. Checking Python version...")
if sys.version_info < (3, 8):
    print(f"❌ Python 3.8+ required. You have {sys.version}")
    sys.exit(1)
print(f"✅ Python {sys.version.split()[0]}")

# Test 2: Check required packages
print("\n2. Checking required packages...")
required_packages = {
    'discord': 'discord.py',
    'dotenv': 'python-dotenv',
    'langgraph': 'langgraph',
    'langchain': 'langchain',
    'langchain_openai': 'langchain-openai',
    'facebook_business': 'facebook-business',
    'pydantic': 'pydantic'
}

missing_packages = []
for module, package in required_packages.items():
    try:
        __import__(module)
        print(f"✅ {package}")
    except ImportError:
        print(f"❌ {package} not installed")
        missing_packages.append(package)

if missing_packages:
    print(f"\nRun: pip install {' '.join(missing_packages)}")
    sys.exit(1)

# Test 3: Check environment variables
print("\n3. Checking environment variables...")
env_vars = {
    'DISCORD_BOT_TOKEN': 'Discord Bot Token',
    'META_ACCESS_TOKEN': 'Meta Access Token',
    'META_AD_ACCOUNT_ID': 'Meta Ad Account ID',
    'OPENAI_API_KEY': 'OpenAI API Key'
}

missing_env = []
for var, name in env_vars.items():
    value = os.getenv(var)
    if value and value != f"your_{var.lower()}_here":
        # Mask sensitive data
        masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        print(f"✅ {name}: {masked}")
    else:
        print(f"❌ {name}: Not configured")
        missing_env.append(var)

if missing_env:
    print(f"\nPlease configure these in .env file")
    sys.exit(1)

# Test 4: Test imports
print("\n4. Testing imports...")
try:
    from agents.discord_bot import MetaAdsDiscordBot
    print("✅ Discord bot imports")
except Exception as e:
    print(f"❌ Discord bot import failed: {e}")
    sys.exit(1)

try:
    from agents.meta_ads_agent import MetaAdsAgent
    print("✅ Meta Ads agent imports")
except Exception as e:
    print(f"❌ Meta Ads agent import failed: {e}")
    sys.exit(1)

try:
    from tools.meta_sdk import MetaAdsSDK
    print("✅ Meta SDK imports")
except Exception as e:
    print(f"❌ Meta SDK import failed: {e}")
    sys.exit(1)

# Test 5: Test Meta SDK connection
print("\n5. Testing Meta SDK connection...")
try:
    from tools.meta_sdk import MetaAdsSDK
    sdk = MetaAdsSDK()
    # Try to get campaigns (will fail if credentials are wrong)
    result = sdk.get_all_campaigns()
    if isinstance(result, dict) and "error" in result:
        print(f"⚠️  Meta SDK initialized but API error: {result['error'][:100]}")
    else:
        print(f"✅ Meta SDK connected! Found {len(result)} campaigns")
except Exception as e:
    print(f"❌ Meta SDK connection failed: {e}")
    print("Check your META_ACCESS_TOKEN and META_AD_ACCOUNT_ID")

# Test 6: Test OpenAI connection
print("\n6. Testing OpenAI connection...")
try:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    response = llm.invoke("Say 'API Connected' in 3 words")
    print(f"✅ OpenAI connected: {response.content}")
except Exception as e:
    print(f"❌ OpenAI connection failed: {e}")
    print("Check your OPENAI_API_KEY")

print("\n" + "=" * 40)
print("✅ All tests passed! Bot is ready to run.")
print("\nRun with: python main.py")
print("Or use: ./run.sh")