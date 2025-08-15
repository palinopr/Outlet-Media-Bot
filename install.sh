#!/bin/bash

# Meta Ads Discord Bot - Installation Script

echo "🚀 Meta Ads Discord Bot - Installation"
echo "======================================"

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python $required_version or higher is required. You have Python $python_version"
    exit 1
fi
echo "✅ Python $python_version found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi
python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ Pip upgraded"

# Install requirements
echo ""
echo "Installing requirements..."
pip install -r requirements.txt
echo "✅ Requirements installed"

# Check .env file
echo ""
echo "Checking configuration..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Creating .env template..."
    cat > .env << EOF
# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Meta/Facebook Ads Configuration
META_ACCESS_TOKEN=your_meta_access_token_here
META_AD_ACCOUNT_ID=your_ad_account_id_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional Configuration
LOG_LEVEL=INFO
META_API_VERSION=v21.0
EOF
    echo "⚠️  .env file created. Please edit it with your credentials!"
else
    echo "✅ .env file found"
    
    # Check if required variables are set
    missing_vars=""
    [ -z "$(grep -E '^DISCORD_BOT_TOKEN=.+' .env)" ] && missing_vars="$missing_vars DISCORD_BOT_TOKEN"
    [ -z "$(grep -E '^META_ACCESS_TOKEN=.+' .env)" ] && missing_vars="$missing_vars META_ACCESS_TOKEN"
    [ -z "$(grep -E '^META_AD_ACCOUNT_ID=.+' .env)" ] && missing_vars="$missing_vars META_AD_ACCOUNT_ID"
    [ -z "$(grep -E '^OPENAI_API_KEY=.+' .env)" ] && missing_vars="$missing_vars OPENAI_API_KEY"
    
    if [ ! -z "$missing_vars" ]; then
        echo "⚠️  Missing configuration for:$missing_vars"
        echo "Please edit .env file with your credentials!"
    else
        echo "✅ All required environment variables appear to be set"
    fi
fi

echo ""
echo "======================================"
echo "✅ Installation complete!"
echo ""
echo "To run the bot:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the bot: python main.py"
echo ""
echo "Or simply run: ./run.sh"