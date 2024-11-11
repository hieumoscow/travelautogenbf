# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes, ActionTypes, SuggestedActions, CardAction
from suggested_actions import get_suggested_actions
from websocket_handler import WebSocketHandler



class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.
    def set_ws_handler(self, ws_handler: WebSocketHandler):
        self.ws_handler = ws_handler

    async def _send_suggested_actions(self, turn_context: TurnContext):
        """Helper method to create and send suggested actions"""
        reply = get_suggested_actions()
        await turn_context.send_activity(reply)

    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text
        value = turn_context.activity.value  # For card responses

        # Handle both regular text and card responses
        message = text if text else value
        if self.ws_handler:
            await self.ws_handler.send_message(message)
        
        # Then show the suggested actions again
        # await self._send_suggested_actions(turn_context)

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                # Welcome message
                welcome_message = Activity(
                    type=ActivityTypes.message,
                    text="Hello! 👋 I'm your travel assistant. Here are some things I can help you with:",
                )
                await turn_context.send_activity(welcome_message)
                
                # Show the suggested actions
                await self._send_suggested_actions(turn_context)