from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount


class L1SupportBot(ActivityHandler):

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("👋 Welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        try:
            user_input = turn_context.activity.text
            print(f"User: {user_input}")

            # TEMP TEST RESPONSE (IMPORTANT)
            await turn_context.send_activity(f"Echo: {user_input}")

        except Exception as e:
            print(f"🔥 BOT ERROR: {str(e)}")
            await turn_context.send_activity("Error occurred")