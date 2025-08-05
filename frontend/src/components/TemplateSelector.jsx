import React from 'react';

export default function TemplateSelector({ templates, selectedTemplate, setSelectedTemplate }) {


  return (
    <div className="template-selector">
      <label>Templates</label>
      <div className="buttons-container">
        
        {templates.map(t => (
          <button
            key={t}
            className={`temp-button${t === selectedTemplate ? ' active' : ''}`}
            
            onClick={() => setSelectedTemplate(t)}
          >
            {t}
          </button>
        ))}
      </div>
    </div>
  );
}
