#!/usr/bin/env python3
"""Start the Discord bot"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import and run the bot
from agents.discord_bot import run
run()