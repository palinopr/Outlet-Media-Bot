"""
Discord Bot for Meta Ads
Simple bot that handles Discord messages and routes them to the Meta Ads agent
"""
import discord
import asyncio
import logging
import os
from typing import Optional
from agents.meta_ads_agent import MetaAdsAgent

logger = logging.getLogger(__name__)


class MetaAdsDiscordBot:
    """Discord bot for Meta Ads interactions"""
    
    def __init__(self):
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        if not self.token:
            raise ValueError("DISCORD_BOT_TOKEN not found")
        
        # Initialize the Meta Ads agent
        self.agent = MetaAdsAgent()
        
        # Setup Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        self.client = discord.Client(intents=intents)
        
        # Setup event handlers
        self.setup_events()
    
    def setup_events(self):
        """Setup Discord event handlers"""
        
        @self.client.event
        async def on_ready():
            logger.info(f'Bot logged in as {self.client.user}')
            await self.client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="Meta Ads campaigns"
                )
            )
        
        @self.client.event
        async def on_message(message: discord.Message):
            # Ignore bot's own messages
            if message.author == self.client.user:
                return
            
            # Respond to mentions or DMs
            is_mention = self.client.user in message.mentions
            is_dm = isinstance(message.channel, discord.DMChannel)
            
            if not (is_mention or is_dm):
                return
            
            await self.handle_message(message)
    
    async def handle_message(self, message: discord.Message):
        """Process incoming message"""
        try:
            # Show typing indicator
            async with message.channel.typing():
                # Clean message content
                content = message.content.replace(f'<@{self.client.user.id}>', '').strip()
                
                if not content:
                    await message.reply(
                        "👋 Hi! I can help you with Meta Ads. Try asking:\n"
                        "• How many campaigns are active?\n"
                        "• Show me campaign performance\n"
                        "• What's the spend today?\n"
                        "• Show CTR for Miami campaign"
                    )
                    return
                
                logger.info(f"User {message.author}: {content[:100]}")
                
                # Process with agent
                try:
                    response = await self.agent.process_request(content)
                    
                    # Handle long messages
                    if len(response) > 2000:
                        # Split into chunks
                        chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                        for i, chunk in enumerate(chunks):
                            if i == 0:
                                await message.reply(chunk)
                            else:
                                await message.channel.send(chunk)
                    else:
                        await message.reply(response)
                        
                except Exception as e:
                    logger.error(f"Agent error: {e}")
                    await message.reply(
                        f"❌ Sorry, I encountered an error:\n```{str(e)[:500]}```\n"
                        "Please try rephrasing your question."
                    )
                    
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            try:
                await message.reply("❌ An unexpected error occurred. Please try again.")
            except:
                pass
    
    async def start(self):
        """Start the bot"""
        await self.client.start(self.token)
    
    def run(self):
        """Run the bot (blocking)"""
        asyncio.run(self.start())


def run():
    """Run the Discord bot"""
    bot = MetaAdsDiscordBot()
    bot.run()


if __name__ == "__main__":
    run()