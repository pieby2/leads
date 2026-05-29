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

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || streaming) return;

    const userMessage: ChatMessageType = { role: 'user', content: trimmed };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setStreaming(true);

    // add empty assistant message that we'll stream into
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
      (citations) => {
        // attach citations to the last message
        setMessages(prev => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === 'assistant' && citations.length > 0) {
            updated[updated.length - 1] = { ...last, citations };
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
          <ChatMessage key={i} message={msg} />
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
