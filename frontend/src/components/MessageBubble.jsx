/**
 * MessageBubble — renders a single chat message.
 * Assistant messages are rendered as full markdown (headings, bold, lists, blockquotes).
 * User messages are plain text.
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const TOOL_META = {
  get_weather: { icon: '🌤️', label: 'Live Weather' },
  get_places:  { icon: '📍', label: 'Places API' },
};

export function MessageBubble({ message }) {
  const isUser = message.role === 'human';

  return (
    <div className={`message-row ${isUser ? 'user' : ''}`}>
      {/* Avatar */}
      <div className={`avatar ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? '👤' : '✈️'}
      </div>

      {/* Bubble */}
      <div className={`bubble ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? (
          // User messages — plain text, preserve newlines
          <span style={{ whiteSpace: 'pre-wrap' }}>{message.content}</span>
        ) : (
          // Assistant messages — full markdown rendering
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Tool call badges */}
        {!isUser && message.toolsUsed && message.toolsUsed.length > 0 && (
          <div className="tools-used">
            {message.toolsUsed.map((t, idx) => {
              const meta = TOOL_META[t.tool] || { icon: '🔧', label: t.tool };
              return (
                <span key={idx} className="tool-badge" title={`Input: ${JSON.stringify(t.input)}`}>
                  <span className="tool-icon">{meta.icon}</span>
                  {meta.label}
                </span>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
