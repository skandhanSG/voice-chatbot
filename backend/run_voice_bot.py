from speech import recognize_speech, speak_text
from language import detect_language
from translator import translate_to_english, translate_from_english
from backend.ai_engine import get_response

def main():
    print("🤖 Voice L1 Support Bot Started (Ctrl + C to exit)\n")

    while True:
        user_input = recognize_speech()

        if not user_input:
            continue

        lang = detect_language(user_input)

        english_text = translate_to_english(user_input, lang)

        response = get_response(english_text)

        final_response = translate_from_english(response, lang)

        print(f"🤖 Bot: {final_response}")

        speak_text(final_response, lang)


if __name__ == "__main__":
    main()