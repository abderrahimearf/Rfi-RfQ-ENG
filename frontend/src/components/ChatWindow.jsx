import React, { useEffect, useRef } from 'react';
import InstructionInput from './InstructionInput';

export default function ChatWindow({ messages, value, onChange, onSend }) {
  const listRef = useRef(null);

  useEffect(() => {
    const listEl = listRef.current;
    if (listEl) {
      listEl.scrollTop = listEl.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="chat-window">
      <div className="message-list" ref={listRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>

      
      <InstructionInput
        value={value}
        onChange={onChange}
        onSend={onSend}
      />
    </div>
  );
}
