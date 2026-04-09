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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
REGION     = os.getenv("AZURE_SPEECH_REGION")


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"


# ─────────────────────────────────────────────────────────────
# Send to Teams via /api/proactive on bot server
# ─────────────────────────────────────────────────────────────
def send_to_teams(user_id: str, payload: dict, label: str = "message"):
    """
    payload can be either:
      { "text": "..." }                    → plain text message
      { "attachment": { ... card ... } }   → adaptive/hero card
    """
    try:
        body = {"user_id": user_id, **payload}
        response = requests.post(
            "http://localhost:3978/api/proactive",
            json=body,
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ Teams [{label}] sent for user: {user_id}")
        elif response.status_code == 404:
            print(f"⚠️  Teams [{label}] — no ConversationReference for: {user_id}")
        else:
            print(f"⚠️  Teams [{label}] status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Teams [{label}] error: {e}")


# ─────────────────────────────────────────────────────────────
# /api/chat
# ─────────────────────────────────────────────────────────────
@app.post("/api/chat")
def chat(req: ChatRequest):
    user_input = req.message
    user_id    = req.user_id

    print(f"\n🎤 Voice input from [{user_id}]: {user_input}")

    # ── Step 1: Send user's voice message as a distinct USER card ──
    # We send it as an Adaptive Card styled to look like a right-aligned
    # user bubble — title "🎤 You said" makes it immediately clear
    user_card = {
        "attachment": {
            "type": "user_voice",          # signal to app.py to render as user card
            "text": user_input
        }
    }
    send_to_teams(user_id, user_card, label="user voice msg")

    # ── Step 2: Language + AI ──────────────────────────────────────
    lang = detect_language(user_input)
    print(f"🌍 Language: {lang}")

    if lang in ["en", "zh-cn", "zh-tw", "zh"]:
        response = get_response(user_input)
    else:
        english  = translate_to_english(user_input, lang)
        response = get_response(english)
        response = translate_from_english(response, lang)

    print(f"🤖 AI response: {response[:80]}...")

    # ── Step 3: Send bot reply as plain text (normal bot bubble) ───
    send_to_teams(user_id, {"text": f"{response}"}, label="bot reply")

    return {"response": response}


# ─────────────────────────────────────────────────────────────
# /api/speech-token
# ─────────────────────────────────────────────────────────────
@app.get("/api/speech-token")
def get_speech_token():
    url = f"https://{REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {"Ocp-Apim-Subscription-Key": SPEECH_KEY}
    response = requests.post(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Speech token error: {response.status_code}")
        return {"error": "Failed to get speech token"}

    return {"token": response.text, "region": REGION}