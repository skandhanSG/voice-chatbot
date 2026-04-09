import React, { useState } from "react";
import "./App.css";
import VoicePopup from "./VoicePopup";
import { speakText } from "./speech";

function App() {
  const [messages, setMessages] = useState([]);
  const [showMic, setShowMic] = useState(false);

  // Add message to chat
  const addMessage = (sender, text) => {
    setMessages((prev) => [...prev, { sender, text }]);
  };

  // Handle voice input result
  const handleVoiceResult = async (text) => {
    // 1. Show user message
    addMessage("You", text);

    // 2. Send to backend
    const res = await fetch("http://localhost:8000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: text }),
    });

    const data = await res.json();

    // ⚠️ handle both keys (your backend may use response or reply)
    const botReply = data.reply || data.response;

    // 3. Show bot response
    addMessage("Bot", botReply);

    // 4. Speak response
    speakText(botReply);
  };

  return (
    <div className="App" style={{ textAlign: "center", marginTop: "50px" }}>
      <h2>🎤 Voice Chatbot</h2>

      {/* Chat Window */}
      <div
        style={{
          border: "1px solid #ccc",
          padding: "10px",
          height: "350px",
          width: "400px",
          margin: "20px auto",
          overflowY: "auto",
          textAlign: "left",
          borderRadius: "10px",
          background: "#f9f9f9",
        }}
      >
        {messages.length === 0 && <p>Start speaking...</p>}

        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: "10px",
              padding: "8px",
              borderRadius: "8px",
              background: msg.sender === "You" ? "#d1e7ff" : "#e2e2e2",
            }}
          >
            <b>{msg.sender}:</b> {msg.text}
          </div>
        ))}
      </div>

      {/* Mic Button */}
      <button
        onClick={() => setShowMic(true)}
        style={{
          padding: "10px 20px",
          fontSize: "16px",
          borderRadius: "8px",
          cursor: "pointer",
        }}
      >
        🎤 Speak
      </button>

      {/* Voice Popup */}
      {showMic && (
        <VoicePopup
          onClose={() => setShowMic(false)}
          onResult={handleVoiceResult}
        />
      )}
    </div>
  );
}

export default App;