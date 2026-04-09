from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

from dotenv import load_dotenv
load_dotenv()

from language import detect_language
from translator import translate_to_english, translate_from_english
from ai_engine import get_response

# ─────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten this to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# ENV
# ─────────────────────────────────────────────────────────────
SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
REGION     = os.getenv("AZURE_SPEECH_REGION")

# ─────────────────────────────────────────────────────────────
# REQUEST MODEL
# user_id added — required to route proactive message back
#    into the correct Teams conversation
# ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"   # Teams user ID passed from React URL param


# ─────────────────────────────────────────────────────────────
# PROACTIVE TEAMS MESSAGING
# Posts to the /api/proactive endpoint on the bot server (app.py)
# which uses the stored ConversationReference to push a message
# into the live Teams conversation.
# ─────────────────────────────────────────────────────────────
def send_to_teams(user_id: str, text: str, label: str = "message"):
    """
    Send a message into a Teams conversation proactively.

    Flow:
      FastAPI (port 8000)
        → POST /api/proactive on bot server (port 3978)
          → ADAPTER.continue_conversation() using stored ConversationReference
            → Teams chat receives the message

    This only works if the user has previously chatted with the bot in Teams
    so a ConversationReference has been saved for their user_id.
    """
    try:
        response = requests.post(
            "http://localhost:3978/api/proactive",
            json={"user_id": user_id, "text": text},
            timeout=5
        )
        if response.status_code == 200:
            print(f"Teams [{label}] sent for user: {user_id}")
        elif response.status_code == 404:
            print(f"Teams [{label}] skipped — no ConversationReference for user: {user_id}")
            print(f"   → User must send at least one message in Teams first.")
        else:
            print(f"Teams [{label}] unexpected status {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"Teams [{label}] — bot server not reachable on port 3978")
    except Exception as e:
        print(f"Teams [{label}] error: {e}")


# ─────────────────────────────────────────────────────────────
# CHAT ENDPOINT
# Called by React voice UI after speech-to-text conversion
# ─────────────────────────────────────────────────────────────
@app.post("/api/chat")
def chat(req: ChatRequest):
    user_input = req.message
    user_id    = req.user_id

    print(f"\n Voice input from user [{user_id}]: {user_input}")

    # Step 1: Post the user's spoken text into Teams chat
    send_to_teams(user_id, f"User - {user_input}", label="user voice msg")

    # Step 2: Language detection + translation + AI
    lang = detect_language(user_input)
    print(f"Detected language: {lang}")

    if lang in ["en", "zh-cn", "zh-tw", "zh"]:
        response = get_response(user_input)
    else:
        english  = translate_to_english(user_input, lang)
        response = get_response(english)
        response = translate_from_english(response, lang)

    print(f"AI response: {response[:80]}...")

    # Step 3: Post the bot's reply into Teams chat too
    send_to_teams(user_id, f"{response}", label="bot reply")

    # Step 4: Return response to React UI (for display + TTS)
    return {"response": response}


# ─────────────────────────────────────────────────────────────
# SPEECH TOKEN ENDPOINT
# React fetches a short-lived token so the API key never
# touches the browser.
# ─────────────────────────────────────────────────────────────
@app.get("/api/speech-token")
def get_speech_token():
    url = f"https://{REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {"Ocp-Apim-Subscription-Key": SPEECH_KEY}
    response = requests.post(url, headers=headers)

    if response.status_code != 200:
        print(f"Speech token error: {response.status_code} {response.text}")
        return {"error": "Failed to get speech token"}, 500

    return {
        "token":  response.text,
        "region": REGION
    }