from botbuilder.schema import Activity, ActivityTypes, Attachment

def get_suggested_actions() -> Activity:
    card = {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "What would you like to know?",
                        "size": "Medium",
                        "weight": "Bolder",
                        "wrap": True
                    }
                ],
                "style": "emphasis",
                "spacing": "medium"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "🏰 What activities can I do in Singapore?",
                "style": "positive",
                "data": "What activities can I do in Singapore?"
            },
            {
                "type": "Action.Submit",
                "title": "🏮 Tell me more about Singapore's culture",
                "data": "Tell me more about Singapore's culture"
            },
            {
                "type": "Action.Submit",
                "title": "🌤️ What's the best time to visit Singapore?",
                "data": "What's the best time to visit Singapore?"
            },
            {
                "type": "Action.Submit",
                "title": "🍜 Recommend some local food in Singapore",
                "data": "Recommend some local food in Singapore"
            }
        ]
    }

    attachment = Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card
    )

    reply = Activity(
        type=ActivityTypes.message,
        attachments=[attachment]
    )
    return reply