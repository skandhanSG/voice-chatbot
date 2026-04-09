import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";

export const speakText = async (text) => {
  const res = await fetch("http://localhost:8000/api/speech-token");
  const tokenData = await res.json();

  const speechConfig = SpeechSDK.SpeechConfig.fromAuthorizationToken(
    tokenData.token,
    tokenData.region
  );

  speechConfig.speechSynthesisLanguage = "en-US";

  const synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig);

  synthesizer.speakTextAsync(text);
};