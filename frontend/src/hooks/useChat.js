/**
 * useChat — custom hook that manages conversation state and API calls.
 *
 * Responsibilities:
 * - Maintain messages array
 * - POST to /chat on the agent backend
 * - Track loading / error state
 * - Expose sendMessage action
 */

import { useState, useCallback } from 'react';

const AGENT_BACKEND_URL = import.meta.env.VITE_AGENT_BACKEND_URL || 'http://localhost:8000';

export function useChat() {
  const [messages, setMessages] = useState([]);    // { id, role, content, toolsUsed? }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Build the history array expected by the backend:
   * only include human/assistant turns (no system messages).
   */
  const buildHistory = (msgs) =>
    msgs.map((m) => ({ role: m.role, content: m.content }));

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || loading) return;
      setError(null);

      // Optimistically add the user's message
      const userMsg = { id: Date.now(), role: 'human', content: text.trim() };
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);

      try {
        const response = await fetch(`${AGENT_BACKEND_URL}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: text.trim(),
            history: buildHistory(messages),   // pass existing history (before new msg)
          }),
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        const assistantMsg = {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.reply,
          toolsUsed: data.tools_used || [],
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        console.error('[useChat] sendMessage error:', err);
        setError(err.message || 'Failed to reach the travel agent. Is the backend running?');
      } finally {
        setLoading(false);
      }
    },
    [messages, loading]
  );

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, sendMessage, clearHistory };
}
