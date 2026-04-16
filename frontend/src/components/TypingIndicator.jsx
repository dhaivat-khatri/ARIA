/** TypingIndicator — three bouncing dots shown while the agent is thinking. */

import React from 'react';

export function TypingIndicator() {
  return (
    <div className="typing-row">
      <div className="avatar assistant">✈️</div>
      <div className="typing-bubble">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  );
}
