from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os

from dotenv import load_dotenv
load_dotenv()

from language import detect_language
from translator import translate_to_english, translate_from_english
from ai_engine import get_response

def send_to_teams(user_text):
    try:
        requests.post(
            "http://localhost:3978/api/messages",
            json={
                "type": "message",
                "text": user_text
            }
        )
    except Exception as e:
        print("❌ Teams send error:", e)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ ENV VARIABLES
SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
REGION = os.getenv("AZURE_SPEECH_REGION")

# print("SPEECH_KEY:", SPEECH_KEY)
# print("REGION:", REGION)



# ✅ REQUEST MODEL
class RequestModel(BaseModel):
    message: str


# ✅ EXISTING CHAT API
@app.post("/api/chat")
def chat(req: RequestModel):
    user_input = req.message

    # 🔥 SEND USER MESSAGE TO TEAMS
    send_to_teams(user_input)

    lang = detect_language(user_input)

    if lang == "en":
        response = get_response(user_input)

    elif lang in ["zh-cn", "zh-tw", "zh"]:
        response = get_response(user_input)

    else:
        english = translate_to_english(user_input, lang)
        response = get_response(english)
        response = translate_from_english(response, lang)

    return {"response": response}


# 🔥🔥 ADD THIS NEW API 🔥🔥
@app.get("/api/speech-token")
def get_speech_token():
    url = f"https://{REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"

    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY
    }

    response = requests.post(url, headers=headers)

    return {
        "token": response.text,
        "region": REGION
    }