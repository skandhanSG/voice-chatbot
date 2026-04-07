import azure.cognitiveservices.speech as speechsdk
from config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION

def recognize_speech():
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION
    )

    speech_config.speech_recognition_language = "en-US"

    audio_config = speechsdk.AudioConfig(use_default_microphone=True)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    print("🎤 Speak now...")

    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"📝 You said: {result.text}")
        return result.text

    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("❌ No speech recognized")
        return None

    else:
        print(f"⚠️ Error: {result.reason}")
        return None

# def speak_text(text, language="en"):
#     speech_config = speechsdk.SpeechConfig(
#         subscription=AZURE_SPEECH_KEY,
#         region=AZURE_SPEECH_REGION
#     )

#     voice_map = {
#         "en": "en-US-AriaNeural",
#         "ta": "ta-IN-PallaviNeural",
#         "hi": "hi-IN-SwaraNeural"
#     }

#     speech_config.speech_synthesis_voice_name = voice_map.get(language, "en-US-AriaNeural")

#     #audio_config = speechsdk.AudioConfig(use_default_speaker=True)
#     audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

#     synthesizer = speechsdk.SpeechSynthesizer(
#         speech_config=speech_config,
#         audio_config=audio_config
#     )

#     synthesizer.speak_text_async(text).get()    

import azure.cognitiveservices.speech as speechsdk
from config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION

def speak_text(text, language="en"):
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION
    )

    voice_map = {
        "en": "en-US-AriaNeural",
        "ta": "ta-IN-PallaviNeural",
        "hi": "hi-IN-SwaraNeural"
    }

    speech_config.speech_synthesis_voice_name = voice_map.get(language, "en-US-AriaNeural")

    # ✅ FIXED LINE
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    synthesizer.speak_text_async(text).get()