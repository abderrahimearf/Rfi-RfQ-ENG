import React from 'react';

export default function DocumentPreview({ fichier }) {
 
  return (
    <div
      className="document-preview"
      style={{
        width: '100%',
      
        height: 'calc(100vh - 200px)', 
        minHeight: '700px', 
        border: '1px solid #e0e0e0',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        backgroundColor: '#f8f9fa' 
      }}
    >
      <iframe
        
        srcDoc={fichier}
        title="Aperçu du document"
        style={{
          width: '100%',
          height: '100%',
          border: 'none' 
        }}
      />
    </div>
  );
}