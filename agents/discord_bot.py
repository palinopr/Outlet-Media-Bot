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

# Check if we should use LangGraph deployment
USE_LANGGRAPH_DEPLOYMENT = os.getenv("USE_LANGGRAPH_DEPLOYMENT", "false").lower() == "true"

if USE_LANGGRAPH_DEPLOYMENT:
    try:
        from langgraph_sdk import get_client
        logger = logging.getLogger(__name__)
        logger.info("LangGraph deployment mode enabled")
    except ImportError:
        logger = logging.getLogger(__name__)
        logger.warning("langgraph-sdk not installed, falling back to local mode")
        USE_LANGGRAPH_DEPLOYMENT = False
else:
    logger = logging.getLogger(__name__)
    logger.info("Using local agent mode (no deployment)")


class MetaAdsDiscordBot:
    """Discord bot for Meta Ads interactions"""
    
    def __init__(self):
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        if not self.token:
            raise ValueError("DISCORD_BOT_TOKEN not found")
        
        # Initialize the agent (local or remote)
        if USE_LANGGRAPH_DEPLOYMENT:
            self._init_remote_agent()
        else:
            self.agent = MetaAdsAgent()
            self.use_remote = False
        
        # Setup Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        self.client = discord.Client(intents=intents)
        
        # Setup event handlers
        self.setup_events()
    
    def _init_remote_agent(self):
        """Initialize connection to LangGraph deployment"""
        deployment_url = os.getenv("LANGGRAPH_DEPLOYMENT_URL")
        api_key = os.getenv("LANGGRAPH_API_KEY")
        
        if not deployment_url or not api_key:
            logger.warning("LangGraph deployment URL or API key missing, using local agent")
            self.agent = MetaAdsAgent()
            self.use_remote = False
            return
        
        try:
            # Create LangGraph client
            self.lg_client = get_client(url=deployment_url, api_key=api_key)
            self.use_remote = True
            self.assistant_id = "meta_ads_agent"  # The graph name from langgraph.json
            logger.info(f"Connected to LangGraph deployment at {deployment_url}")
        except Exception as e:
            logger.error(f"Failed to connect to LangGraph deployment: {e}")
            logger.info("Falling back to local agent")
            self.agent = MetaAdsAgent()
            self.use_remote = False
    
    async def process_with_remote(self, content: str) -> str:
        """Process request using remote LangGraph deployment"""
        try:
            # Create a thread for this conversation
            thread = await self.lg_client.threads.create()
            thread_id = thread["thread_id"]
            
            # Stream the run
            input_data = {
                "messages": [{"role": "human", "content": content}],
                "current_request": content
            }
            
            # Use the runs.stream method to process
            final_output = None
            async for chunk in self.lg_client.runs.stream(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                input=input_data,
                stream_mode="values"
            ):
                if chunk and isinstance(chunk, dict):
                    # Look for final_answer in the output
                    if "final_answer" in chunk:
                        final_output = chunk["final_answer"]
                    # Also check in the data field
                    elif "data" in chunk and isinstance(chunk["data"], dict):
                        if "final_answer" in chunk["data"]:
                            final_output = chunk["data"]["final_answer"]
            
            if final_output:
                return final_output
            else:
                # Fallback: try to get the last message from the thread
                state = await self.lg_client.threads.get_state(thread_id)
                if state and "values" in state and "final_answer" in state["values"]:
                    return state["values"]["final_answer"]
                return "I processed your request but couldn't generate a proper response."
                
        except Exception as e:
            logger.error(f"Remote processing error: {e}", exc_info=True)
            # Fallback to local processing
            logger.info("Falling back to local processing")
            return await self.agent.process_request(content)
    
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
                
                # Process with agent (remote or local)
                try:
                    if self.use_remote:
                        logger.info("Processing with remote LangGraph deployment")
                        response = await self.process_with_remote(content)
                    else:
                        logger.info("Processing with local agent")
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
                    logger.error(f"Agent error: {e}", exc_info=True)
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