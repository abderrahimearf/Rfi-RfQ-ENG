import React, { useRef, useEffect } from 'react';

export default function InstructionInput({ value, onChange, onSend }) {
  const textareaRef = useRef(null);

  useEffect(() => {
    
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + "px";
  }, [value]);

  return (
    <div className="instruction-input">
      <textarea
        ref={textareaRef}
        placeholder="Écrivez votre instruction..."
        value={value}
        onChange={e => onChange(e.target.value)}
        rows={1} 
      />
      <button className="send-button" onClick={() => {
          if (value.trim()) {
            onSend();
          }
        }}
      >↗</button>
    </div>
  );
}
