#!/bin/bash

# Deploy to LangGraph Cloud

echo "🚀 Deploying to LangGraph Cloud"
echo "================================"

# Check if langgraph CLI is installed
if ! command -v langgraph &> /dev/null; then
    echo "Installing LangGraph CLI..."
    pip install langgraph-cli
fi

# Check environment variables
if [ -z "$LANGSMITH_API_KEY" ]; then
    echo "❌ LANGSMITH_API_KEY not set!"
    echo "Export it first: export LANGSMITH_API_KEY=your_key"
    exit 1
fi

# Test the graph locally first
echo ""
echo "Testing graph locally..."
python3 graph.py > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Graph test failed! Fix errors before deploying."
    exit 1
fi
echo "✅ Graph test passed"

# Deploy to LangGraph Cloud
echo ""
echo "Deploying to LangGraph Cloud..."
langgraph deploy --config langgraph.json

echo ""
echo "✅ Deployment complete!"
echo ""
echo "View your deployment at:"
echo "  https://smith.langchain.com"