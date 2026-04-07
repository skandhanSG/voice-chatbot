import React, { useState } from "react";
import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";

function App() {
  const [text, setText] = useState("");
  const [response, setResponse] = useState("");

  const speechKey = process.env.AZURE_SPEECH_KEY;
  const region = process.env.AZURE_SPEECH_REGION;

  const startListening = () => {
    const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(speechKey, region);
    speechConfig.speechRecognitionLanguage = "en-US";

    const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
    const recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

    recognizer.recognizeOnceAsync(async (result) => {
      if (result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
        setText(result.text);

        // 🔥 Send to backend
        const res = await fetch("http://localhost:8000/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ message: result.text })
        });

        const data = await res.json();
        setResponse(data.response);

        speak(data.response);
      }
    });
  };

  const speak = (text) => {
    const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(speechKey, region);
    speechConfig.speechSynthesisVoiceName = "en-US-AriaNeural";

    const synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig);
    synthesizer.speakTextAsync(text);
  };

  return (
    <div style={{ textAlign: "center", marginTop: "100px" }}>
      <h1>🎤 Voice Assistant</h1>
      <button onClick={startListening}>Start Speaking</button>

      <p><b>You:</b> {text}</p>
      <p><b>Bot:</b> {response}</p>
    </div>
  );
}

export default App;