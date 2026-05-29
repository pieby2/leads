import { ChatMessage as ChatMessageType } from '@/types';

interface ChatMessageProps {
  message: ChatMessageType;
}

// Parse citation references like [A:chunk_3] from the text
function parseCitations(content: string) {
  const parts: (string | { video: string; chunk: string })[] = [];
  const regex = /\[([AB]):chunk_(\d+)\]/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }
    parts.push({ video: match[1], chunk: match[2] });
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return parts;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  const renderContent = () => {
    if (isUser) return message.content;

    const parts = parseCitations(message.content);
    return parts.map((part, i) => {
      if (typeof part === 'string') return <span key={i}>{part}</span>;
      return (
        <span
          key={i}
          className={`citation-badge citation-${part.video.toLowerCase()}`}
          title={`Source: Video ${part.video}, Chunk ${part.chunk}`}
        >
          {part.video}:{part.chunk}
        </span>
      );
    });
  };

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <span className="message-role">
        {isUser ? 'You' : 'VidCompare AI'}
      </span>
      <div className="message-bubble">
        {renderContent()}
      </div>
      {/* External citations from the SSE response */}
      {message.citations && message.citations.length > 0 && (
        <div className="message-citations">
          {message.citations.map((c, i) => (
            <span
              key={i}
              className={`citation-badge citation-${(c.video_id || 'a').toLowerCase()}`}
            >
              📄 {c.video_id}:chunk_{c.chunk_index}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
