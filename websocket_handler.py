"""Handles WebSocket connections and message processing"""
import logging
import os
from azure.messaging.webpubsubservice import WebPubSubServiceClient
import websockets
import asyncio
import json
from datetime import datetime, timedelta
from botbuilder.schema import (
    ConversationReference, 
    ConversationAccount, 
    ChannelAccount
)

from bot_handler import BotHandler
from message_formatter import DEFAULT_ACTIONS

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
        self.reconnect_attempt = 0
        self.max_reconnect_attempts = 10  # Maximum number of quick reconnection attempts
        self.last_reconnect_time = None
        self.heartbeat_task = None
        self.is_processing = False  # Add this line to track message processing state
        LOG.info("WebSocket handler initialized")

        # Create a complete default conversation reference with all required fields
        service_url = os.getenv('SERVICE_URL', 'http://localhost:3978')
        if 'WEBSITE_HOSTNAME' in os.environ:
            service_url = f"https://{os.environ['WEBSITE_HOSTNAME']}"
        self.default_conversation_reference = ConversationReference(
            channel_id="emulator",
            service_url=service_url,
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

    def get_backoff_time(self) -> float:
        """Calculate exponential backoff time with a maximum"""
        if self.last_reconnect_time:
            # Reset reconnect attempts if last attempt was more than 5 minutes ago
            time_since_last = datetime.now() - self.last_reconnect_time
            if time_since_last > timedelta(minutes=5):
                self.reconnect_attempt = 0

        # Exponential backoff with max of 30 seconds
        backoff = min(30, (2 ** self.reconnect_attempt))
        return backoff

    async def heartbeat(self):
        """Send periodic heartbeat to keep connection alive"""
        while self.connection and not self.connection.closed:
            try:
                await self.connection.ping()
                await asyncio.sleep(20)  # Send heartbeat every 20 seconds
            except Exception as e:
                LOG.warning(f"Heartbeat failed: {str(e)}")
                break
        LOG.info("Heartbeat task ended")

    async def connect(self):
        """Establish WebSocket connection with retry logic"""
        if self.reconnect_attempt >= self.max_reconnect_attempts:
            LOG.error("Maximum reconnection attempts reached. Waiting longer before trying again.")
            await asyncio.sleep(300)  # Wait 5 minutes before resetting
            self.reconnect_attempt = 0
            return False

        try:
            # Get a fresh token URL each time we connect
            client_access_token = self.service.get_client_access_token()
            test_url = os.getenv('WEBSOCKET_URL', client_access_token['url'])
            logging.info(f"Connecting to {test_url}")
            self.connection = await websockets.connect(
                test_url, #client_access_token['url'],
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
                max_size=10_000_000,  # 10MB max message size
                extra_headers={
                    "User-Agent": "TravelBot/1.0",
                    "Connection": "keep-alive"
                }
            )

            # Start heartbeat task
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            self.heartbeat_task = asyncio.create_task(self.heartbeat())

            LOG.info("Connected to Web PubSub service")
            self.reconnect_attempt = 0
            return True

        except Exception as e:
            LOG.error(f"Failed to connect to WebSocket: {str(e)}")
            self.reconnect_attempt += 1
            self.last_reconnect_time = datetime.now()
            backoff_time = self.get_backoff_time()
            LOG.info(f"Will attempt reconnect in {backoff_time} seconds (attempt {self.reconnect_attempt})")
            return False

    def format_message_with_actions(self, message: str) -> dict:
        """Format the message to include suggested actions"""
        try:
            message_data = json.loads(message)
            if 'suggested_actions' not in message_data:
                message_data['suggested_actions'] = DEFAULT_ACTIONS
            return json.dumps(message_data)
        except json.JSONDecodeError:
            return json.dumps({
                "message": message,
                "agent": "AutoGen Agent",
                "suggested_actions": DEFAULT_ACTIONS
            })

    async def send_message(self, message: str):
        """Send a message over the WebSocket connection with retry logic"""
        if not self.connection or self.connection.closed:
            LOG.warning("No WebSocket connection available, attempting to reconnect...")
            if not await self.connect():
                LOG.error("Failed to establish connection for sending message")
                return

        try:
            if isinstance(message, (dict, list)):
                message_to_send = json.dumps(message)
            else:
                message_to_send = str(message)  # Ensure string conversion

            LOG.debug(f"Sending serialized message: {message_to_send}")
            await self.connection.send(message_to_send)
            LOG.info(f"Sent message: {message}")
        except Exception as e:
            LOG.error(f"Error sending message: {str(e)}")
            self.connection = None
            # Try to reconnect and resend
            if await self.connect():
                try:
                    await self.connection.send(message)
                    LOG.info("Successfully resent message after reconnection")
                except Exception as resend_error:
                    LOG.error(f"Failed to resend message after reconnection: {str(resend_error)}")

    async def receive_messages(self):
        """Main message receiving loop with improved error handling"""
        while self.should_reconnect:
            try:
                if not self.connection or self.connection.closed:
                    backoff_time = self.get_backoff_time()
                    await asyncio.sleep(backoff_time)
                    
                    if not await self.connect():
                        continue

                async for message in self.connection:
                    LOG.info(f"Received message: {message}")
                    
                    # Show typing indicator before processing
                    if not self.is_processing:
                        self.is_processing = True
                        await self.bot_handler.bot_adapter.continue_conversation(
                            self.bot_handler.last_conversation_reference,
                            self.bot_handler.show_typing,
                            self.bot_handler.app_id
                        )

                    formatted_message = self.format_message_with_actions(message)
                    await self.bot_handler.process_websocket_message(formatted_message)
                    self.is_processing = False

            except websockets.exceptions.ConnectionClosed as closed_error:
                self.is_processing = False  # Reset processing state on connection close
                LOG.warning(f"WebSocket connection closed ({closed_error.code}): {closed_error.reason}")
                self.connection = None
            except Exception as e:
                self.is_processing = False  # Reset processing state on error
                LOG.error(f"Error in receive_messages: {str(e)}")
                self.connection = None

    def get_task(self, app):
        """Create background task for the application"""
        return asyncio.create_task(self.receive_messages())

    async def cleanup(self):
        """Cleanup WebSocket connection and tasks"""
        self.should_reconnect = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        if self.connection:
            await self.connection.close()