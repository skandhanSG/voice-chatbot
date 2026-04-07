import requests
import os

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount

from language import detect_language
from translator import translate_to_english, translate_from_english
from ai_engine import get_response
from speech import speech_to_text_from_file  # you need this
from botbuilder.schema import HeroCard, CardAction, ActionTypes, Attachment

class L1SupportBot(ActivityHandler):

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:

                card = HeroCard(
                    title="👋 Welcome to IT Support",
                    text="How would you like to continue?",
                    buttons=[
                        CardAction(
                            type=ActionTypes.im_back,
                            title="💬 Text Support",
                            value="text support"
                        ),
                        CardAction(
                            type=ActionTypes.open_url,
                            title="🎤 Voice Support",
                            value="http://localhost:3000"
                        )
                    ]
                )

                attachment = Attachment(
                    content_type="application/vnd.microsoft.card.hero",
                    content=card
                )

                await turn_context.send_activity(
                    {"attachments": [attachment]}
                )

    async def send_welcome_card(self, turn_context):
        from botbuilder.schema import HeroCard, CardAction, ActionTypes, Attachment

        card = HeroCard(
            title="👋 Welcome to IT Support",
            text="Choose how you want support:",
            buttons=[
                CardAction(
                    type=ActionTypes.im_back,
                    title="💬 Text Support",
                    value="text support"
                ),
                CardAction(
                    type=ActionTypes.open_url,
                    title="🎤 Voice Support",
                    value="http://localhost:3000"
                )
            ]
        )

        attachment = Attachment(
            content_type="application/vnd.microsoft.card.hero",
            content=card
        )

        await turn_context.send_activity({"attachments": [attachment]})

    async def on_message_activity(self, turn_context: TurnContext):
        try:
            user_input = turn_context.activity.text.lower()

            # 👇 Handle button click
            if user_input == "text support":
                await turn_context.send_activity("💬 How can I assist you today?")
                return
            
            if user_input in ["hi", "hello", "start"]:
                await self.send_welcome_card(turn_context)
                return

            if "voice" in user_input:
                await turn_context.send_activity(
                    "🎤 Click here to start voice support:\nhttp://localhost:3000"
                )
                return  

            # 👇 Normal flow
            lang = detect_language(user_input)
            english_text = translate_to_english(user_input, lang)
            response = get_response(english_text)
            final_response = translate_from_english(response, lang)

            await turn_context.send_activity(final_response)

        except Exception as e:
            print(f"🔥 BOT ERROR: {str(e)}")
            await turn_context.send_activity("⚠️ Error occurred.")    