from fastapi import FastAPI
from pydantic import BaseModel

from backend.language import detect_language
from backend.translator import translate_to_english, translate_from_english
from backend.ai_engine import get_response

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ ADD THIS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestModel(BaseModel):
    message: str


@app.post("/api/chat")
def chat(req: RequestModel):
    user_input = req.message

    lang = detect_language(user_input)
    english = translate_to_english(user_input, lang)
    response = get_response(english)
    final = translate_from_english(response, lang)

    return {"response": final}