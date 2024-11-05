# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import traceback
import uuid
from dotenv import load_dotenv
from datetime import datetime
from aiohttp import web
from botbuilder.core import TurnContext
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes

from bot import MyBot
from config import DefaultConfig
import os
from bot_handler import BotHandler
from websocket_handler import WebSocketHandler

CONFIG = DefaultConfig()
load_dotenv()

# Create adapter
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))

# Setup WebSocket handler
conn_str = os.environ.get('WEBPUBSUB_CONNECTION_STRING1')
if not conn_str:
    raise ValueError("Missing WEBPUBSUB_CONNECTION_STRING1 environment variable")

# Catch-all for errors
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )

    if context.activity.channel_id == "emulator":
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        await context.send_activity(trace_activity)

ADAPTER.on_turn_error = on_error

# Create the Bot
BOT = MyBot()

APP_ID = CONFIG.APP_ID if CONFIG.APP_ID else uuid.uuid4()

# Setup routes and handlers
APP = web.Application(middlewares=[aiohttp_error_middleware])
bot_handler = BotHandler(ADAPTER, APP_ID, BOT)
APP.router.add_post("/api/messages", bot_handler.messages)

# Setup WebSocket handler and background tasks
websocket_handler = WebSocketHandler(conn_str, 'Hub', bot_handler)

async def start_background_tasks(app):
    app['websocket_task'] = websocket_handler.get_task(app)

async def cleanup_background_tasks(app):
    app['websocket_task'].cancel()
    await websocket_handler.cleanup()

APP.on_startup.append(start_background_tasks)
APP.on_cleanup.append(cleanup_background_tasks)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error