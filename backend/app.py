import os
from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, MessageFactory
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes, Attachment, CardImage
from botbuilder.schema import HeroCard, CardAction, ActionTypes
from botframework.connector.auth import ClaimsIdentity
from dotenv import load_dotenv

load_dotenv()

from bot import L1SupportBot, conversation_references

APP_ID       = os.getenv("MICROSOFT_APP_ID", "")
APP_PASSWORD = os.getenv("MICROSOFT_APP_PASSWORD", "")

SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER  = BotFrameworkAdapter(SETTINGS)
BOT      = L1SupportBot()


async def on_error(context, error):
    print(f"🔥 BOT ERROR: {error}")
    await context.send_activity("⚠️ Bot encountered an error.")

ADAPTER.on_turn_error = on_error


# ─────────────────────────────────────────────────────────────
# /api/messages
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
        print(f"🔥 APP ERROR: {str(e)}")
        return web.Response(status=500, text=str(e))


# ─────────────────────────────────────────────────────────────
# /api/proactive
#
# Accepts two payload shapes from FastAPI:
#
#   1. Plain bot reply:
#      { "user_id": "...", "text": "bot answer here" }
#      → Sent as a normal bot message bubble
#
#   2. User voice message card:
#      { "user_id": "...", "attachment": { "type": "user_voice", "text": "..." } }
#      → Rendered as a HeroCard with a distinct header so it's visually
#        separated from the bot reply and clearly labelled as the user's input
#
# WHY a card for the user message?
#   Both messages are technically sent BY THE BOT (proactive messaging).
#   Teams/Emulator always shows bot-sent messages on the LEFT side.
#   We cannot fake a right-side user bubble from the bot's context.
#   The best UX solution is a styled card with a clear "🎤 You said:" header
#   so users instantly understand which is their input vs the bot's reply.
# ─────────────────────────────────────────────────────────────
async def send_proactive(req: web.Request) -> web.Response:
    try:
        body    = await req.json()
        user_id = body.get("user_id")
        text    = body.get("text")
        attachment_data = body.get("attachment")  # present for user voice msg

        if not user_id:
            return web.Response(status=400, text="'user_id' is required")

        conversation_ref = conversation_references.get(user_id)

        if not conversation_ref:
            msg = (
                f"No ConversationReference for user: {user_id}. "
                f"User must send at least one message in Teams/Emulator first."
            )
            print(f"⚠️  {msg}")
            return web.Response(status=404, text=msg)

        # ── Build the activity to send ────────────────────────────
        if attachment_data and attachment_data.get("type") == "user_voice":
            # Render user's spoken text as a visually distinct HeroCard
            spoken_text = attachment_data.get("text", "")

            hero_card = HeroCard(
                # Title clearly labels this as the USER's voice input
                title="🎤  You said",
                # The spoken text is the card subtitle
                text=spoken_text,
            )

            activity_to_send = MessageFactory.attachment(
                Attachment(
                    content_type="application/vnd.microsoft.card.hero",
                    content=hero_card,
                )
            )

        elif text:
            # Plain bot reply — standard message
            activity_to_send = MessageFactory.text(text)

        else:
            return web.Response(status=400, text="Either 'text' or 'attachment' is required")

        # ── Send via continue_conversation ────────────────────────
        async def _send(turn_context):
            await turn_context.send_activity(activity_to_send)

        # ClaimsIdentity bypasses the `if not bot_id` falsy-string check
        # that causes "Expected bot_id or claims_identity" when APP_ID = ""
        claims_identity = ClaimsIdentity(
            claims={"aud": APP_ID, "iss": APP_ID},
            is_authenticated=True
        )

        await ADAPTER.continue_conversation(
            conversation_ref,
            _send,
            claims_identity=claims_identity
        )

        print(f"✅ Proactive message sent → Teams | user: {user_id}")
        return web.Response(status=200, text="OK")

    except Exception as e:
        print(f"🔥 PROACTIVE ERROR: {str(e)}")
        return web.Response(status=500, text=str(e))


# ─────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────
app = web.Application(middlewares=[aiohttp_error_middleware])
app.router.add_post("/api/messages",  messages)
app.router.add_post("/api/proactive", send_proactive)

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=3978)