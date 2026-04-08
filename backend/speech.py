import azure.cognitiveservices.speech as speechsdk
from . import config

AZURE_SPEECH_KEY = config.AZURE_SPEECH_KEY  
AZURE_SPEECH_REGION = config.AZURE_SPEECH_REGION

def speech_to_text_from_file(file_path):
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION
    )

    audio_config = speechsdk.AudioConfig(filename=file_path)

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text

    return None