#!/bin/bash

# Meta Ads Discord Bot - Run Script

echo "🤖 Starting Meta Ads Discord Bot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running installation..."
    ./install.sh
    if [ $? -ne 0 ]; then
        echo "Installation failed. Please fix the issues and try again."
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists and has required variables
if [ ! -f ".env" ]; then
    echo "❌ .env file not found! Run ./install.sh first"
    exit 1
fi

# Run the bot
echo "Starting bot..."
python main.py