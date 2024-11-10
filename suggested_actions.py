# shared/suggested_actions.py
from botbuilder.schema import Activity, ActivityTypes, SuggestedActions, CardAction, ActionTypes

def get_suggested_actions() -> Activity:
    """Creates an Activity with suggested actions"""
    return Activity(
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