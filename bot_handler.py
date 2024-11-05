"""Handles bot operations and message processing"""
import logging
import json
from aiohttp.web import Request, Response, json_response
from botbuilder.schema import Activity, ActivityTypes, ConversationReference, ChannelAccount, ConversationParameters
from typing import Optional
from botbuilder.core import (
    TurnContext,
)
from botbuilder.integration.aiohttp import CloudAdapter

LOG = logging.getLogger(__name__)

class BotHandler:
    def __init__(self, bot_adapter: CloudAdapter, app_id: str, bot):
        self.bot_adapter = bot_adapter
        self.app_id = app_id
        self.bot = bot
        self.last_conversation_reference: Optional[ConversationReference] = None

    def create_conversation(self) -> ConversationReference:
        conversationParam = ConversationParameters(is_group=False, bot=self.bot, members=[ChannelAccount(id=self.app_id)],)
        conversationReference = self.bot_adapter.create_conversation(self.app_id, self.bot,conversationParam)
        return conversationReference
    

    async def messages(self, req: Request) -> Response:
        """Handle incoming HTTP requests on /api/messages"""
        # Print header & body for debugging
        raw_body = await req.read()
        print(req.headers["Content-Type"])
        print(raw_body)

        # Main bot message handler
        if "application/json" in req.headers["Content-Type"]:
            body = await req.json()
        else:
            return Response(status=415)

        activity = Activity().deserialize(body)
        
        # Store the conversation reference
        self.last_conversation_reference = TurnContext.get_conversation_reference(activity)
        
        auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

        response = await self.bot_adapter.process(req, self.bot)
        if response:
            return json_response(data=response.body, status=response.status)
        return Response(status=201)

    async def process_websocket_message(self, message: str):
        """Process incoming WebSocket messages"""
        if not self.last_conversation_reference:
            LOG.warning("No conversation reference available - message cannot be processed")
            return

        try:
            # Parse message as JSON
            try:
                message_data = json.loads(message)
                text = message_data.get('message', '')
                agent_name = message_data.get('agent', 'AutoGen Agent')
                LOG.info(f"Processing message from agent: {agent_name}")
            except json.JSONDecodeError:
                text = message
                agent_name = 'AutoGen Agent'

            async def callback(context: TurnContext):
                # Create a proper Activity object
                message_activity = Activity(
                    type=ActivityTypes.message,
                    text=text,
                    from_property=ChannelAccount(
                        id=f"agent-{agent_name.lower().replace(' ', '-')}",
                        name=agent_name
                    )
                )
                await context.send_activity(message_activity)
            await self.bot_adapter.continue_conversation(
                self.last_conversation_reference, 
                callback,
                self.app_id
            )
        except Exception as e:
            LOG.error(f"Error processing WebSocket message: {str(e)}")
            raise