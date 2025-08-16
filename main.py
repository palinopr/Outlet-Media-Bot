#!/usr/bin/env python3
"""
Meta Ads Discord Bot - Main Entry Point
Simple bot that responds to Discord messages about Meta Ads
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
if os.getenv("LANGCHAIN_PROJECT"):
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    from agents.discord_bot import run
    
    # Check for required environment variables
    required_vars = [
        "DISCORD_BOT_TOKEN",
        "META_ACCESS_TOKEN", 
        "META_AD_ACCOUNT_ID",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please check your .env file")
        sys.exit(1)
    
    logger.info("Starting Meta Ads Discord Bot...")
    
    # Log LangSmith status
    if os.getenv("LANGCHAIN_TRACING_V2") == "true":
        logger.info(f"✅ LangSmith tracing enabled - Project: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
    else:
        logger.warning("⚠️ LangSmith tracing is disabled")
    
    try:
        # Run the Discord bot
        run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()