import React, { useEffect, useRef } from "react";
import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";

const VoicePopup = ({ onClose, onResult }) => {
  const hasRecognized = useRef(false);
  const recognizerRef = useRef(null);

  useEffect(() => {
    startListening();

    return () => {
      // 🔥 DO NOT call close again if already used
      if (recognizerRef.current) {
        try {
          recognizerRef.current.stopContinuousRecognitionAsync();
        } catch (e) {}
      }
    };
  }, []);

  const startListening = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/speech-token");
      const tokenData = await res.json();

      const speechConfig = SpeechSDK.SpeechConfig.fromAuthorizationToken(
        tokenData.token,
        tokenData.region
      );

      speechConfig.speechRecognitionLanguage = "en-US";

      const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();

      const recognizer = new SpeechSDK.SpeechRecognizer(
        speechConfig,
        audioConfig
      );

      recognizerRef.current = recognizer;

      recognizer.recognizeOnceAsync((result) => {
        if (hasRecognized.current) return;
        hasRecognized.current = true;

        if (result.text) {
          onResult(result.text); // 🔥 important
        }

        // 🔥 DO NOT call close() here
        onClose();
      });

    } catch (err) {
      console.error("Speech error:", err);
      onClose();
    }
  };

  return (
    <div style={overlay}>
      <div style={popup}>
        <h3>🎤 Listening...</h3>
        <div style={mic}>🎤</div>
        <p>Speak now...</p>
        <button onClick={onClose}>Cancel</button>
      </div>
    </div>
  );
};

const overlay = {
  position: "fixed",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  background: "rgba(0,0,0,0.5)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
};

const popup = {
  background: "#fff",
  padding: "20px",
  borderRadius: "10px",
  textAlign: "center",
};

const mic = {
  fontSize: "40px",
  margin: "10px",
};

export default VoicePopup;