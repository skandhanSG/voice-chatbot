import sys
from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity

from bot import L1SupportBot

# ✅ Adapter setup
SETTINGS = BotFrameworkAdapterSettings("", "")
ADAPTER = BotFrameworkAdapter(SETTINGS)

BOT = L1SupportBot()

# ✅ Error handler (VERY IMPORTANT)
async def on_error(context, error):
    print(f"🔥 BOT ERROR: {error}")
    await context.send_activity("⚠️ Bot encountered an error.")

ADAPTER.on_turn_error = on_error


# ✅ Messages endpoint
async def messages(req: web.Request) -> web.Response:
    try:
        if "application/json" not in req.headers.get("Content-Type", ""):
            return web.Response(status=415)

        body = await req.json()

        # ✅ FIX: Convert to Activity object
        activity = Activity().deserialize(body)

        auth_header = req.headers.get("Authorization", "")

        await ADAPTER.process_activity(
            activity,
            auth_header,
            BOT.on_turn,
        )

        return web.Response(status=201)

    except Exception as e:
        print(f"🔥 APP ERROR: {str(e)}")
        return web.Response(status=500, text=str(e))


# ✅ App init
app = web.Application(middlewares=[aiohttp_error_middleware])
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=3978)