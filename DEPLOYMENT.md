# Deployment Guide - Meta Ads Discord Bot

## 🚀 Quick Start (Local)

```bash
# 1. Install and run
./install.sh
./run.sh
```

## 📋 Prerequisites

- Python 3.8+
- Discord Bot Token
- Meta/Facebook App credentials
- OpenAI API Key

## 🔧 Setup Instructions

### 1. Get Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application
3. Go to "Bot" section
4. Click "Reset Token" and copy it
5. Enable these Intents:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT

### 2. Get Meta/Facebook Credentials

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create an App (Business type)
3. Add "Marketing API" product
4. Get your Access Token:
   - Go to Tools → Access Token Tool
   - Generate User Token with `ads_management` permission
5. Get your Ad Account ID:
   - Go to Business Settings
   - Find your Ad Account ID (numbers only, no 'act_' prefix)

### 3. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create API Key
3. Copy the key

### 4. Configure Environment

Edit `.env` file:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=123456789  # numbers only
OPENAI_API_KEY=sk-...
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t meta-ads-bot .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## ☁️ Cloud Deployment Options

### Option 1: VPS (DigitalOcean, Linode, etc.)

```bash
# SSH into your VPS
ssh user@your-server

# Clone the code
git clone your-repo
cd meta-agent-2

# Install and run
./install.sh
nohup ./run.sh > bot.log 2>&1 &
```

### Option 2: AWS EC2

1. Launch EC2 instance (t2.micro is enough)
2. Security Group: No inbound rules needed (bot only makes outbound connections)
3. SSH and setup:
```bash
# Install Python
sudo yum install python3 git -y

# Clone and setup
git clone your-repo
cd meta-agent-2
./install.sh

# Run with systemd (create service file)
sudo nano /etc/systemd/system/meta-ads-bot.service
```

Service file:
```ini
[Unit]
Description=Meta Ads Discord Bot
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/meta-agent-2
Environment="PATH=/home/ec2-user/meta-agent-2/venv/bin"
ExecStart=/home/ec2-user/meta-agent-2/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl enable meta-ads-bot
sudo systemctl start meta-ads-bot
sudo systemctl status meta-ads-bot
```

### Option 3: Railway/Render (Easy)

1. Connect GitHub repo
2. Add environment variables in dashboard
3. Deploy automatically

### Option 4: Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT-ID/meta-ads-bot

# Deploy
gcloud run deploy --image gcr.io/PROJECT-ID/meta-ads-bot --platform managed
```

## 🔍 Testing

```bash
# Test setup
python test_setup.py

# Test bot locally
python main.py
```

## 📊 Monitoring

### Check Bot Status
- In Discord: Bot should show "Watching Meta Ads campaigns"
- Logs: Check `bot.log` or console output

### Common Issues

1. **Bot not responding**
   - Check bot has permissions in Discord server
   - Verify MESSAGE CONTENT INTENT is enabled
   - Check logs for errors

2. **Meta API errors**
   - Verify Access Token hasn't expired
   - Check Ad Account ID format (numbers only)
   - Ensure token has `ads_management` permission

3. **OpenAI errors**
   - Check API key is valid
   - Verify you have credits/billing set up

## 🔐 Security Best Practices

1. **Never commit `.env` file**
2. **Use environment variables in production**
3. **Rotate tokens regularly**
4. **Use read-only Meta access if only querying**
5. **Set up monitoring/alerts**

## 📈 Performance

- Bot uses ~100-200MB RAM
- Minimal CPU usage (spikes only when processing)
- Can handle multiple concurrent requests
- Response time: 1-3 seconds typically

## 🆘 Support

Check logs first:
```bash
# Docker logs
docker-compose logs -f

# Local logs
tail -f bot.log

# Test setup
python test_setup.py
```

## 🔄 Updates

```bash
# Pull latest code
git pull

# Reinstall dependencies
./install.sh

# Restart bot
./run.sh

# Or with Docker
docker-compose down
docker-compose up -d --build
```