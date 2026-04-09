from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount

from language import detect_language
from translator import translate_to_english, translate_from_english
from backend.ai_engine import get_response


class L1SupportBot(ActivityHandler):

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Welcome to L1 Support Bot!")

    async def on_message_activity(self, turn_context: TurnContext):
        try:
            user_input = turn_context.activity.text
            print(f"\n User: {user_input}")

            # 🌍 Detect language
            lang = detect_language(user_input)
            print(f"🌍 Language: {lang}")

            # 🔁 Translate to English
            english_text = translate_to_english(user_input, lang)
            print(f"🇬🇧 English: {english_text}")

            # 🤖 AI response
            response = get_response(english_text)
            print(f"🤖 AI: {response}")

            # 🔁 Translate back
            final_response = translate_from_english(response, lang)

            print(f"📤 Final: {final_response}")

            await turn_context.send_activity(final_response)

        except Exception as e:
            print(f"🔥 BOT ERROR: {str(e)}")
            await turn_context.send_activity("⚠️ Sorry, something went wrong.")