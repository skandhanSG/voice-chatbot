def detect_language(text):
    try:
        from langdetect import detect

        lang = detect(text)

        # ✅ Force English if mostly ASCII (very important)
        if text.isascii():
            return "en"

        return lang

    except:
        return "en"