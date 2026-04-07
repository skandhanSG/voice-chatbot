import requests
import os

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount

from backend.language import detect_language
from backend.translator import translate_to_english, translate_from_english
from backend.ai_engine import get_ai_response
from backend.speech import speech_to_text_from_file  # you need this


class L1SupportBot(ActivityHandler):

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("👋 Welcome to L1 Support Bot!")

    async def on_message_activity(self, turn_context: TurnContext):
        try:
            user_input = turn_context.activity.text
            attachments = turn_context.activity.attachments

            # 🎤 CASE 1: Voice Message
            if attachments:
                await turn_context.send_activity("🎧 Processing your voice message...")

                audio_url = attachments[0].content_url
                print(f"Audio URL: {audio_url}")

                # Download file
                file_path = "input_audio.wav"

                headers = {}
                if turn_context.activity.service_url:
                    headers = {"Authorization": f"Bearer {turn_context.adapter._credentials.microsoft_app_password}"}

                response = requests.get(audio_url)

                with open(file_path, "wb") as f:
                    f.write(response.content)

                # Convert speech → text
                user_input = speech_to_text_from_file(file_path)
                print(f"📝 Converted Text: {user_input}")

                if not user_input:
                    await turn_context.send_activity("❌ Could not understand audio.")
                    return

            # 💬 CASE 2: Normal Text
            if not user_input:
                await turn_context.send_activity("Please send a message.")
                return

            print(f"🧑 User: {user_input}")

            # 🌍 Language detection
            lang = detect_language(user_input)

            # 🔁 Translate
            english_text = translate_to_english(user_input, lang)

            # 🤖 AI
            response = get_ai_response(english_text)

            # 🔁 Translate back
            final_response = translate_from_english(response, lang)

            await turn_context.send_activity(final_response)

        except Exception as e:
            print(f"🔥 BOT ERROR: {str(e)}")
            await turn_context.send_activity("⚠️ Error processing request.")