# Meta Ads Discord Bot

A simple Discord bot that uses LangGraph to intelligently respond to questions about Meta Ads campaigns.

## Structure

```
Meta agent 2/
├── main.py              # Discord bot entry point
├── graph.py             # LangGraph Cloud entry point
├── langgraph.json       # LangGraph deployment config
├── agents/
│   ├── discord_bot.py   # Discord bot handler
│   └── meta_ads_agent.py # LangGraph agent with thinking capability
├── tools/
│   └── meta_sdk.py      # Simple Meta Ads SDK wrapper
├── config/
│   └── settings.py      # Configuration management
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
└── deploy_langgraph.sh  # Deploy to LangGraph Cloud
```

## Features

- **Simple & Clean**: ~700 lines of code total (vs 10,000+ before)
- **Smart Agent**: Uses GPT-4 to understand requests and decide what to query
- **Direct SDK Access**: Simple wrapper around Facebook Business SDK
- **Discord Integration**: Responds to mentions and DMs
- **LangGraph Ready**: Deploy to LangGraph Cloud/Studio
- **LangSmith Tracing**: Full observability of agent actions

## Setup

### Quick Start
```bash
./install.sh   # Install dependencies
./run.sh       # Run Discord bot
```

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env` file:
```env
# Required
DISCORD_BOT_TOKEN=your_discord_token
META_ACCESS_TOKEN=your_meta_token
META_AD_ACCOUNT_ID=your_account_id
OPENAI_API_KEY=your_openai_key

# LangSmith (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=MetaAdsBot
```

3. Run the bot:
```bash
# Discord Bot
python main.py

# Local Testing (no Discord)
python run_local.py

# Test Setup
python test_setup.py
```

## Usage

In Discord, mention the bot or DM it:
- "How many active campaigns do I have?"
- "Show me today's spend"
- "What's the CTR for Miami campaign?"
- "Show campaign performance"

## How It Works

1. **Discord Bot** receives message
2. **LangGraph Agent** understands the request using GPT-4
3. **Meta SDK** queries the Facebook API
4. **Agent** formats the response nicely
5. **Discord Bot** sends the formatted reply

## Architecture

```
User Message → Discord Bot → LangGraph Agent → Meta SDK → Facebook API
                                   ↓
                                 GPT-4
                              (understands)
```

## Deployment

### LangGraph Cloud
```bash
# Deploy to LangGraph Cloud
./deploy_langgraph.sh

# Or manually
langgraph deploy --config langgraph.json
```

### Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

### Cloud Platforms
- **Railway/Render**: Connect GitHub repo
- **AWS/GCP**: Use Docker or systemd service
- **VPS**: Run with `nohup ./run.sh &`

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Testing

```bash
# Test everything works
python test_setup.py

# Test with LangSmith tracing
python test_langsmith_local.py

# Interactive local testing
python run_local.py --mode interactive
```

## Files

- **Core**: 700 lines total
- **Tests**: Full test coverage
- **Deployment**: Docker, LangGraph, Cloud ready
- **Documentation**: Complete setup & deployment guides

Simple, clean, and production-ready!