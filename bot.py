# bot.py
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
from suggested_actions import get_suggested_actions

class MyBot(ActivityHandler):
    def set_ws_handler(self, ws_handler):
        self.ws_handler = ws_handler

    async def on_message_activity(self, turn_context: TurnContext):
        if self.ws_handler:
            await self.ws_handler.send_message(turn_context.activity.text)
        
        # Show the suggested actions
        await turn_context.send_activity(get_suggested_actions())

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
                await turn_context.send_activity(get_suggested_actions())