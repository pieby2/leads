'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { streamChat } from '@/lib/api';
import ChatMessage from './ChatMessage';
import { ChatMessage as ChatMessageType } from '@/types';

interface ChatPanelProps {
  sessionId: string;
}

const WELCOME_MESSAGE: ChatMessageType = {
  role: 'assistant',
  content: "I've analyzed both videos. Ask me anything — try \"Compare engagement rates\" or \"Which video has a better hook?\"",
};

export default function ChatPanel({ sessionId }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // auto-scroll when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

  // auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || streaming) return;

    const userMessage: ChatMessageType = { role: 'user', content: trimmed };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setStreaming(true);

    let assistantContent = '';
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    await streamChat(
      sessionId,
      trimmed,
      (token) => {
        assistantContent += token;
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, content: assistantContent };
          }
          return updated;
        });
      },
      (citations, suggestedQuestions) => {
        // attach citations to the last message
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, citations, suggested_questions: suggestedQuestions };
          }
          return updated;
        });
        setStreaming(false);
      },
      (error) => {
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant') {
            updated[updated.length - 1] = {
              ...last,
              content: `Sorry, something went wrong: ${error}`,
            };
          }
          return updated;
        });
        setStreaming(false);
      }
    );
  };

  const handleSend = () => sendMessage(input);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="glass-card-static chat-panel animate-slide-up delay-3">
      <div className="chat-header">
        <span className="chat-header-dot" />
        <span className="chat-header-title">AI Analysis Chat</span>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i}>
            <ChatMessage message={msg} />
            {msg.suggested_questions && msg.suggested_questions.length > 0 && (
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginLeft: '2.5rem', marginTop: '0.5rem', marginBottom: '1rem' }}>
                {msg.suggested_questions.map((q, qIdx) => (
                  <button
                    key={qIdx}
                    onClick={() => sendMessage(q)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '16px',
                      padding: '0.4rem 0.8rem',
                      color: 'var(--text-secondary)',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseOver={e => {
                      e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                      e.currentTarget.style.color = '#fff';
                    }}
                    onMouseOut={e => {
                      e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {streaming && messages[messages.length - 1]?.content === '' && (
          <div className="typing-indicator">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          ref={textareaRef}
          className="chat-input"
          placeholder="Ask about the videos..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={streaming}
          rows={1}
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={streaming || !input.trim()}
          title="Send message"
        >
          ↑
        </button>
      </div>
    </div>
  );
}
