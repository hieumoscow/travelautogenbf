"""Handles WebSocket connections and message processing"""
import logging
from azure.messaging.webpubsubservice import WebPubSubServiceClient
import websockets
import asyncio
import json
from botbuilder.schema import ConversationReference, ConversationAccount, ChannelAccount


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
# set log basic to print to console
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class WebSocketHandler:
    def __init__(self, connection_string: str, hub_name: str, bot_handler):
        """Initialize WebSocket handler with connection details and bot handler"""
        self.service = WebPubSubServiceClient.from_connection_string(
            connection_string=connection_string, 
            hub=hub_name
        )
        self.client_access_url = self.service.get_client_access_token()
        self.bot_handler = bot_handler
        self.connection = None
        LOG.info("WebSocket handler initialized")

        # Create a complete default conversation reference with all required fields
        self.default_conversation_reference = ConversationReference(
            channel_id="emulator",
            service_url="http://localhost:50428",  # Add a dummy service URL
            conversation=ConversationAccount(
                id="websocket-conversation",
                name="WebSocket Conversation",
                conversation_type="personal"
            ),
            user=ChannelAccount(
                id="websocket-user",
                name="WebSocket User",
                role="user"
            ),
            bot=ChannelAccount(
                id="websocket-bot",
                name="WebSocket Bot",
                role="bot"
            ),
            activity_id="websocket-activity",
            locale="en-US"
        )
        
        # Set it in the bot handler
        self.bot_handler.last_conversation_reference = self.default_conversation_reference

    async def connect(self):
        """Establish WebSocket connection"""
        try:
            self.connection = await websockets.connect(self.client_access_url['url'])
            LOG.info("Connected to Web PubSub service")
            initial_message = {
                "message": "👋 Hello! I'm your AI Assistant. The WebSocket connection is now established and I'm ready to help you with travel planning. What would you like to know?",
                "agent": "System"
            }
            # await self.process_initial_message(json.dumps(initial_message))
            return True
        except Exception as e:
            LOG.error(f"Failed to connect to WebSocket: {str(e)}")
            return False
        
    async def process_initial_message(self, message: str):
        """Process the initial welcome message"""
        try:
            await self.bot_handler.process_websocket_message(message)
            LOG.info("Sent initial welcome message")
        except Exception as e:
            LOG.error(f"Error sending initial message: {str(e)}")

    async def receive_messages(self):
        """Main message receiving loop"""
        while True:
            try:
                if not self.connection:
                    if not await self.connect():
                        await asyncio.sleep(5)
                        continue

                message = await self.connection.recv()
                LOG.info(f"Received message: {message}")
                await self.bot_handler.process_websocket_message(message)

            except websockets.exceptions.ConnectionClosed:
                LOG.warning("WebSocket connection closed. Attempting to reconnect...")
                self.connection = None
                await asyncio.sleep(5)
            except Exception as e:
                LOG.error(f"Error in receive_messages: {str(e)}")
                await asyncio.sleep(5)

    def get_task(self, app):
        """Create background task for the application"""
        return asyncio.create_task(self.receive_messages())

    async def cleanup(self):
        """Cleanup WebSocket connection"""
        if self.connection:
            await self.connection.close()