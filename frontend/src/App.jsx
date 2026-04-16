/**
 * App — root component of the AI Travel Assistant.
 *
 * Layout:
 *   Header → Suggestion pills → Scrollable messages → Input bar
 */

import React, { useRef, useEffect, useState } from 'react';
import { useChat } from './hooks/useChat';
import { MessageBubble } from './components/MessageBubble';
import { TypingIndicator } from './components/TypingIndicator';

// Quick-start suggestion prompts shown before the first message
const SUGGESTIONS = [
  '🌤️ What\'s the weather in Tokyo?',
  '🗺️ Best places to visit in Paris',
  '✈️ Plan a weekend in Barcelona',
  '🍜 Food spots in Bangkok',
  '❄️ Is it cold in Reykjavik right now?',
];

export default function App() {
  const { messages, loading, error, sendMessage, clearHistory } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    sendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e) => {
    // Send on Enter, allow Shift+Enter for newline
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestion = (text) => {
    // Strip emoji prefix before sending
    const clean = text.replace(/^[\p{Emoji}\s]+/u, '').trim();
    sendMessage(clean);
  };

  const hasMessages = messages.length > 0;

  return (
    <>
      {/* Ambient background */}
      <div className="ambient-orb orb-1" aria-hidden="true" />
      <div className="ambient-orb orb-2" aria-hidden="true" />

      <div className="app-shell">
        {/* ── Header ──────────────────────────────────────────────────── */}
        <header className="header">
          <div className="header-logo" aria-hidden="true">✈️</div>
          <div>
            <div className="header-title">ARIA</div>
            <div className="header-subtitle">Agentic Real-time Intelligence Assistant</div>
          </div>
          <div className="status-dot">Live</div>
          {hasMessages && (
            <button
              id="clear-history-btn"
              onClick={clearHistory}
              style={{
                marginLeft: '8px',
                background: 'transparent',
                border: '1px solid var(--border)',
                color: 'var(--text-muted)',
                borderRadius: '8px',
                padding: '5px 12px',
                fontSize: '0.75rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontFamily: 'var(--font-body)',
              }}
              onMouseEnter={(e) => { e.target.style.borderColor = 'var(--accent-1)'; e.target.style.color = 'var(--accent-1)'; }}
              onMouseLeave={(e) => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--text-muted)'; }}
            >
              Clear
            </button>
          )}
        </header>

        {/* ── Suggestion pills (show only with no messages) ─────────── */}
        {!hasMessages && (
          <nav className="suggestions" aria-label="Quick start suggestions">
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                id={`suggestion-${i}`}
                className="suggestion-pill"
                onClick={() => handleSuggestion(s)}
              >
                {s}
              </button>
            ))}
          </nav>
        )}

        {/* ── Messages ──────────────────────────────────────────────── */}
        <main className="messages-area" aria-live="polite" aria-label="Conversation">
          {!hasMessages && (
            <div className="welcome-state">
              <div className="welcome-globe" aria-hidden="true">🌍</div>
              <h1 className="welcome-title">Where to next?</h1>
              <p className="welcome-desc">
                Ask me about weather conditions, must-see attractions, local food, or let me
                plan your next adventure — I combine live data from multiple sources in real time.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {loading && <TypingIndicator />}

          <div ref={messagesEndRef} />
        </main>

        {/* ── Error banner ─────────────────────────────────────────── */}
        {error && (
          <div className="error-banner" role="alert">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* ── Input bar ────────────────────────────────────────────── */}
        <div className="input-bar">
          <form className="input-form" onSubmit={handleSubmit} aria-label="Chat input">
            <textarea
              id="chat-input"
              ref={textareaRef}
              className="input-field"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about any city — weather, places, travel tips…"
              rows={1}
              disabled={loading}
              aria-label="Chat message input"
            />
            <button
              id="send-btn"
              type="submit"
              className="send-btn"
              disabled={!input.trim() || loading}
              aria-label="Send message"
            >
              {loading ? '⏳' : '➤'}
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
