from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import HeroCard, CardAction, ActionTypes, Attachment, Activity

from language import detect_language
from translator import translate_to_english, translate_from_english
from ai_engine import get_response


# Global store for conversation references
# Key:   Teams user ID  (turn_context.activity.from_property.id)
# Value: ConversationReference object (contains service_url, conversation, recipient)
#
# This is what enables proactive messaging — without this, the bot has no
# way to reach back into a Teams conversation from an external trigger (voice UI).
#
# NOTE: In production, replace this dict with Azure Cosmos DB or Azure Cache for Redis
#       so references survive bot restarts and scale across multiple instances.
conversation_references = {}


class L1SupportBot(ActivityHandler):

    # ──────────────────────────────────────────────
    # LIFECYCLE: User joins the Teams conversation
    # ──────────────────────────────────────────────
    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:

                # Save reference immediately when user first appears
                self._save_conversation_reference(turn_context)

                # Send welcome card with Text and Voice options
                await self._send_welcome_card(turn_context)

    # ──────────────────────────────────────────────
    # MAIN: Handle every incoming Teams message
    # ──────────────────────────────────────────────
    async def on_message_activity(self, turn_context: TurnContext):
        try:
            # Always refresh the stored reference on every message
            # This ensures service_url stays current (Teams can rotate it)
            self._save_conversation_reference(turn_context)

            user_input = turn_context.activity.text

            # Guard: no text in activity (e.g. card click with no value)
            if not user_input:
                await turn_context.send_activity("Please send a valid text message.")
                return

            user_input_lower = user_input.strip().lower()

            # ── Button / keyword routing ──────────────────────────────
            if user_input_lower in ["hi", "hello", "start"]:
                await self._send_welcome_card(turn_context)
                return

            if user_input_lower == "text support":
                await turn_context.send_activity("How can I assist you today?")
                return

            if "voice" in user_input_lower:
                # Embed Teams user ID in the URL so React knows who to sync with
                user_id = turn_context.activity.from_property.id
                voice_url = f"http://localhost:3000?userId={user_id}"
                await turn_context.send_activity(
                    f"Click here to open Voice Support:\n{voice_url}"
                )
                return

            # ── AI Flow ───────────────────────────────────────────────
            lang = detect_language(user_input)
            english_text = translate_to_english(user_input, lang)
            ai_response = get_response(english_text)
            final_response = translate_from_english(ai_response, lang)

            await turn_context.send_activity(final_response)

        except Exception as e:
            print(f"BOT ERROR: {str(e)}")
            await turn_context.send_activity("Bot encountered an error. Please try again.")

    # ──────────────────────────────────────────────
    # HELPER: Save ConversationReference
    # ──────────────────────────────────────────────
    def _save_conversation_reference(self, turn_context: TurnContext):
        """
        Extract and store the ConversationReference from the current activity.

        ConversationReference contains everything the adapter needs to send
        a proactive message into this specific Teams conversation later:
          - service_url  (Teams endpoint to POST replies to)
          - conversation (conversation ID + tenant ID)
          - bot          (recipient details)
          - user         (from_property details)
          - channel_id   (e.g. 'msteams')
          - locale
        """
        conversation_ref = TurnContext.get_conversation_reference(turn_context.activity)
        user_id = turn_context.activity.from_property.id

        conversation_references[user_id] = conversation_ref

        print(f"   Saved ConversationReference for user: {user_id}")
        print(f"   service_url : {conversation_ref.service_url}")
        print(f"   conversation: {conversation_ref.conversation.id}")

    # ──────────────────────────────────────────────
    # HELPER: Send Welcome HeroCard
    # ──────────────────────────────────────────────
    async def _send_welcome_card(self, turn_context: TurnContext):
        """
        Send a HeroCard with Text Support and Voice Support buttons.
        Voice Support button URL includes the Teams user ID so the React
        voice UI can sync messages back into this exact conversation.
        """
        user_id = turn_context.activity.from_property.id
        voice_url = f"http://localhost:3000?userId={user_id}"

        card = HeroCard(
            title="Welcome to On Lok's IT Support",
            text="How would you like to get support today?",
            buttons=[
                CardAction(
                    type=ActionTypes.im_back,
                    title="Text Support",
                    value="text support"
                ),
                CardAction(
                    type=ActionTypes.open_url,
                    title="Voice Support",
                    value=voice_url  # user ID embedded here
                )
            ]
        )

        attachment = Attachment(
            content_type="application/vnd.microsoft.card.hero",
            content=card
        )

        await turn_context.send_activity(
            Activity(type="message", attachments=[attachment])
        )