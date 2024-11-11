# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes, ActionTypes, SuggestedActions, CardAction
from websocket_handler import WebSocketHandler



class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.
    def set_ws_handler(self, ws_handler: WebSocketHandler):
        self.ws_handler = ws_handler

    async def _send_suggested_actions(self, turn_context: TurnContext):
        """Helper method to create and send suggested actions"""
        reply = Activity(
            type=ActivityTypes.message,
            suggested_actions=SuggestedActions(
                actions=[
                    CardAction(
                        title="What activities can I do in Singapore?",
                        type=ActionTypes.im_back,
                        value="What activities can I do in Singapore?"
                    ),
                    CardAction(
                        title="Tell me more about Singapore's culture",
                        type=ActionTypes.im_back,
                        value="Tell me more about Singapore's culture"
                    ),
                    CardAction(
                        title="What's the best time to visit Singapore?",
                        type=ActionTypes.im_back,
                        value="What's the best time to visit Singapore?"
                    ),
                    CardAction(
                        title="Recommend some local food in Singapore",
                        type=ActionTypes.im_back,
                        value="Recommend some local food in Singapore"
                    )
                ]
            )
        )
        await turn_context.send_activity(reply)

    async def on_message_activity(self, turn_context: TurnContext):
        # First, send the response to the user's message
        # await turn_context.send_activity(f"You said '{ turn_context.activity.text }'")
        if self.ws_handler:
            await self.ws_handler.send_message(turn_context.activity.text)
        
        # Then show the suggested actions again
        await self._send_suggested_actions(turn_context)

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                # Welcome message
                welcome_message = Activity(
                    text="Hello! 👋 I'm your travel assistant. Here are some things I can help you with:",
                )
                await turn_context.send_activity(welcome_message)
                
                # Show the suggested actions
                await self._send_suggested_actions(turn_context)