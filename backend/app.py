import os
from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity
from botframework.connector.auth import ClaimsIdentity
from dotenv import load_dotenv

load_dotenv()

from bot import L1SupportBot, conversation_references

# ─────────────────────────────────────────────────────────────
# Credentials
# Local Emulator → both stay ""  (empty string)
# Production     → set MICROSOFT_APP_ID + MICROSOFT_APP_PASSWORD in .env
# ─────────────────────────────────────────────────────────────
APP_ID       = os.getenv("MICROSOFT_APP_ID", "")
APP_PASSWORD = os.getenv("MICROSOFT_APP_PASSWORD", "")

SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER  = BotFrameworkAdapter(SETTINGS)
BOT      = L1SupportBot()


async def on_error(context, error):
    print(f"BOT ERROR: {error}")
    await context.send_activity("Bot encountered an error.")

ADAPTER.on_turn_error = on_error


# ─────────────────────────────────────────────────────────────
# Build the ClaimsIdentity used for proactive messaging.
#
# WHY ClaimsIdentity instead of bot_id (app_id string)?
#
#   continue_conversation() validates:
#       if not bot_id and not claims_identity:
#           raise Exception("Expected bot_id or claims_identity")
#
#   When APP_ID = "" (Emulator / no auth), "" is FALSY in Python,
#   so `not bot_id` is True → the check always fails.
#
#   The correct fix for unauthenticated / Emulator mode is to pass a
#   ClaimsIdentity directly. The SDK accepts this and skips the
#   bot_id string validation entirely.
#
#   For production (real Teams with App ID):
#     The ClaimsIdentity below will still work because we embed
#     APP_ID in the claims. No code change needed when you go live.
# ─────────────────────────────────────────────────────────────
def _build_claims_identity() -> ClaimsIdentity:
    """
    Build a ClaimsIdentity for proactive messaging.
    - is_authenticated=True  → tells the SDK this is a trusted internal call
    - claims dict             → "aud" (audience) = APP_ID
                                "iss" (issuer)   = APP_ID
    For Emulator both are "" which is fine — the SDK doesn't validate
    the claim values themselves, only that a ClaimsIdentity object exists.
    """
    claims = {
        "aud": APP_ID,   # audience
        "iss": APP_ID,   # issuer
    }
    return ClaimsIdentity(claims=claims, is_authenticated=True)


# ─────────────────────────────────────────────────────────────
# /api/messages  — receives all Teams / Emulator messages
# ─────────────────────────────────────────────────────────────
async def messages(req: web.Request) -> web.Response:
    try:
        if "application/json" not in req.headers.get("Content-Type", ""):
            return web.Response(status=415)

        body        = await req.json()
        activity    = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")

        await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        return web.Response(status=201)

    except Exception as e:
        print(f"APP ERROR: {str(e)}")
        return web.Response(status=500, text=str(e))


# ─────────────────────────────────────────────────────────────
# /api/proactive  — called by FastAPI to push a message into
#                   a live Teams / Emulator conversation
# ─────────────────────────────────────────────────────────────
async def send_proactive(req: web.Request) -> web.Response:
    try:
        body    = await req.json()
        user_id = body.get("user_id")
        text    = body.get("text")

        if not user_id or not text:
            return web.Response(status=400, text="'user_id' and 'text' are required")

        conversation_ref = conversation_references.get(user_id)

        if not conversation_ref:
            msg = (
                f"No ConversationReference for user: {user_id}. "
                f"User must send at least one message to the bot first."
            )
            print(f"Error: {msg}")
            return web.Response(status=404, text=msg)

        async def _send(turn_context):
            await turn_context.send_activity(text)

        # THE FIX: use ClaimsIdentity instead of bot_id string
        # This bypasses the `if not bot_id` falsy-string check in the SDK
        claims_identity = _build_claims_identity()

        await ADAPTER.continue_conversation(
            conversation_ref,
            _send,
            claims_identity=claims_identity   # keyword arg — not positional
        )

        print(f"Proactive message sent → Teams | user: {user_id}")
        return web.Response(status=200, text="OK")

    except Exception as e:
        print(f"PROACTIVE ERROR: {str(e)}")
        return web.Response(status=500, text=str(e))


# ─────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────
app = web.Application(middlewares=[aiohttp_error_middleware])
app.router.add_post("/api/messages",  messages)
app.router.add_post("/api/proactive", send_proactive)

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=3978)