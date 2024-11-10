"""Handles WebSocket connections and message processing"""
import logging
from azure.messaging.webpubsubservice import WebPubSubServiceClient
import websockets
import asyncio
import json
from botbuilder.schema import (
    ConversationReference, 
    ConversationAccount, 
    ChannelAccount,
    SuggestedActions,
    CardAction,
    ActionTypes
)

from bot_handler import BotHandler

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

DEFAULT_ACTIONS = [
    {
        "title": "What activities can I do in Singapore?",
        "value": "What activities can I do in Singapore?"
    },
    {
        "title": "Tell me more about Singapore's culture",
        "value": "Tell me more about Singapore's culture"
    },
    {
        "title": "What's the best time to visit Singapore?",
        "value": "What's the best time to visit Singapore?"
    },
    {
        "title": "Recommend some local food in Singapore",
        "value": "Recommend some local food in Singapore"
    }
]

class WebSocketHandler:
    def __init__(self, connection_string: str, hub_name: str, bot_handler: BotHandler):
        """Initialize WebSocket handler with connection details and bot handler"""
        self.service = WebPubSubServiceClient.from_connection_string(
            connection_string=connection_string, 
            hub=hub_name
        )
        self.bot_handler = bot_handler
        self.connection = None
        self.should_reconnect = True
        LOG.info("WebSocket handler initialized")

        # Create a complete default conversation reference with all required fields
        self.default_conversation_reference = ConversationReference(
            channel_id="emulator",
            service_url="http://localhost:50428",
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
        
        self.bot_handler.last_conversation_reference = self.default_conversation_reference

    def format_message_with_actions(self, message: str) -> dict:
        """Format the message to include suggested actions"""
        try:
            # Try to parse as JSON first
            message_data = json.loads(message)
            # If no suggested_actions in the message, add default ones
            if 'suggested_actions' not in message_data:
                message_data['suggested_actions'] = DEFAULT_ACTIONS
            return json.dumps(message_data)
        except json.JSONDecodeError:
            # If not JSON, wrap it in a proper format
            return json.dumps({
                "message": message,
                "agent": "AutoGen Agent",
                "suggested_actions": DEFAULT_ACTIONS
            })

    async def connect(self):
        """Establish WebSocket connection"""
        try:
            # Get a fresh token URL each time we connect
            client_access_token = self.service.get_client_access_token()
            test_url = ""
            self.connection = await websockets.connect(
                client_access_token['url'], #test_url,
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=10    # Wait 10 seconds for pong response
            )
            LOG.info("Connected to Web PubSub service: " + client_access_token['url'])
            return True
        except Exception as e:
            LOG.error(f"Failed to connect to WebSocket: {str(e)}")
            return False

    async def send_message(self, message: str):
        """Send a message over the WebSocket connection"""
        if not self.connection:
            LOG.error("No WebSocket connection available")
            return
        
        try:
            await self.connection.send(message)
            LOG.info(f"Sent message: {message}")
        except websockets.exceptions.ConnectionClosed:
            LOG.warning("Connection closed while sending message. Will reconnect on next attempt.")
            self.connection = None
        except Exception as e:
            LOG.error(f"Error sending message: {str(e)}")
            self.connection = None

    async def receive_messages(self):
        """Main message receiving loop"""
        while self.should_reconnect:
            try:
                if not self.connection:
                    if not await self.connect():
                        await asyncio.sleep(5)
                        continue

                async for message in self.connection:
                    LOG.info(f"Received message: {message}")
                    # Format message to include suggested actions
                    formatted_message = self.format_message_with_actions(message)
                    await self.bot_handler.process_websocket_message(formatted_message)

            except websockets.exceptions.ConnectionClosed:
                LOG.warning("WebSocket connection closed. Attempting to reconnect...")
                self.connection = None
                await asyncio.sleep(5)
            except Exception as e:
                LOG.error(f"Error in receive_messages: {str(e)}")
                self.connection = None
                await asyncio.sleep(5)

    def get_task(self, app):
        """Create background task for the application"""
        return asyncio.create_task(self.receive_messages())

    async def cleanup(self):
        """Cleanup WebSocket connection"""
        self.should_reconnect = False
        if self.connection:
            await self.connection.close()