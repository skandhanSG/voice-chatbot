import React, { useState } from "react";
import VoicePopup from "./VoicePopup";
import { speakText } from "./speech";

// ─────────────────────────────────────────────────────────────
// Read Teams user ID from URL param injected by the bot's
// welcome card:  http://localhost:3000?userId=<teams_user_id>
//
// This ID links every voice interaction back to the correct
// Teams conversation so messages appear in both places.
// ─────────────────────────────────────────────────────────────
const params = new URLSearchParams(window.location.search);
const userId = params.get("userId") || "default_user";

// ─────────────────────────────────────────────────────────────
// Inject spinner keyframe once
// ─────────────────────────────────────────────────────────────
if (!document.getElementById("__spin_style__")) {
  const s = document.createElement("style");
  s.id = "__spin_style__";
  s.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
  document.head.appendChild(s);
}

// ─────────────────────────────────────────────────────────────
// App — renders a compact 2×2 inch mic button only.
// No chat window — all conversation happens in Teams chat.
// ─────────────────────────────────────────────────────────────
function App() {
  const [showMic, setShowMic]     = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus]       = useState("");
  const [hover, setHover]         = useState(false);

  const handleVoiceResult = async (text) => {
    if (!text) return;

    setIsLoading(true);
    setStatus(`📝 "${text}"`);

    try {
      // POST to FastAPI which will:
      //  1. Push user's spoken text → Teams chat (🎤 prefix)
      //  2. Get AI response
      //  3. Push AI response → Teams chat (🤖 prefix)
      //  4. Return response text to us for TTS playback
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          user_id: userId,  // ✅ links this voice turn to the Teams conversation
        }),
      });

      if (!res.ok) {
        const errBody = await res.text();
        throw new Error(`Backend ${res.status}: ${errBody}`);
      }

      const data = await res.json();
      const botReply = data.reply || data.response;

      if (!botReply) throw new Error("Empty response from backend");

      // ✅ Speak the bot reply via Azure TTS
      setStatus("🔊 Speaking response...");
      await speakText(botReply);

      setStatus("✅ Done — tap mic to speak again");

    } catch (err) {
      console.error("❌ Voice chat error:", err);
      setStatus("⚠️ Error — check console & try again");
    } finally {
      setIsLoading(false);
    }
  };

  // ── Styles (inline — no extra CSS file needed) ─────────────

  const pageStyle = {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    background: "#f0f2f5",
    fontFamily: "'Segoe UI', Tahoma, sans-serif",
    margin: 0,
    padding: 0,
  };

  // 192px ≈ 2 inches at standard 96 dpi screen
  const cardStyle = {
    width: "192px",
    height: "192px",
    background: "#ffffff",
    borderRadius: "16px",
    boxShadow: hover && !isLoading
      ? "0 6px 28px rgba(0,120,212,0.30)"
      : "0 4px 20px rgba(0,0,0,0.10)",
    border: hover && !isLoading
      ? "2px solid #0078d4"
      : "2px solid transparent",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    cursor: isLoading ? "not-allowed" : "pointer",
    opacity: isLoading ? 0.6 : 1,
    transform: hover && !isLoading ? "scale(1.04)" : "scale(1)",
    transition: "all 0.18s ease",
    userSelect: "none",
  };

  const spinnerStyle = {
    width: "40px",
    height: "40px",
    border: "4px solid #e1dfdd",
    borderTop: "4px solid #0078d4",
    borderRadius: "50%",
    animation: "spin 0.75s linear infinite",
  };

  const statusStyle = {
    fontSize: "12px",
    color: "#605e5c",
    marginTop: "18px",
    maxWidth: "220px",
    textAlign: "center",
    lineHeight: 1.5,
  };

  return (
    <div style={pageStyle}>

      {/* ── 2×2 inch Mic Card ─────────────────────────────── */}
      <div
        style={cardStyle}
        onClick={() => !isLoading && setShowMic(true)}
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        title="Click to speak to IT Support"
      >
        {isLoading ? (
          <>
            <div style={spinnerStyle} />
            <span style={{ fontSize: "12px", fontWeight: 600, color: "#323130" }}>
              Processing...
            </span>
          </>
        ) : (
          <>
            <span style={{ fontSize: "52px", lineHeight: 1 }}>🎤</span>
            <span style={{ fontSize: "13px", fontWeight: 700, color: "#323130" }}>
              Tap to Speak
            </span>
            <span style={{ fontSize: "11px", color: "#605e5c" }}>
              IT Support
            </span>
          </>
        )}
      </div>

      {/* ── Status feedback ───────────────────────────────── */}
      {status && <p style={statusStyle}>{status}</p>}

      {/* ── Recording popup ───────────────────────────────── */}
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