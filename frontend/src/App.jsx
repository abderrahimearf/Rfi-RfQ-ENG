import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import TemplateSelector from './components/TemplateSelector';
import DocumentPreview from './components/DocumentPreview';
import ChatWindow from './components/ChatWindow';
import './App.css';
import { useNavigate } from 'react-router-dom';


// Remplace les placeholders {{ key }} dans le HTML par jsonData[key].contenu
function prepareHtml(htmlTemplate, jsonData) {
  if (!htmlTemplate || !jsonData) return '';
  let processedHtml = htmlTemplate;
  for (const key in jsonData) {
    if (Object.hasOwnProperty.call(jsonData, key)) {
      const placeholder = new RegExp('{{ ' + key + ' }}', 'g');
      const value = jsonData[key].contenu;
      processedHtml = processedHtml.replace(placeholder, value);
    }
  }
  return processedHtml;
}

export default function App() {
  // --- 1. DÉCLARATION DES ÉTATS ---

  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [htmlTemplate, setHtmlTemplate] = useState('');
  const [json, setJson] = useState(null);
  const [fichier, setFichier] = useState('');

  // États pour le ChatWindow
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Bonjour ! Sélectionnez un template pour commencer.' }
  ]);
  const [inputValue, setInputValue] = useState('');

  // --- 2. GESTION DE L'ENVOI DE MESSAGE ---
  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage = { role: 'user', content: inputValue };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: inputValue })
      });
      const data = await response.json();
      const assistantMessage = { role: 'assistant', content: data.response };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Erreur de communication avec le serveur :', error);
    }
  };

  // --- 3. EFFETS (LOGIQUE DE L'APPLICATION) ---

  // Effet #1 : charge la liste des templates
  useEffect(() => {
    fetch('/api/templates-files')
      .then(res => res.json())
      .then(data => setTemplates(data.templates || []))
      .catch(err => console.error('Erreur de chargement de la liste des templates :', err));
  }, []);

  useEffect(() => {
    if (!selectedTemplate) return;
    const fetchDocumentContent = async () => {
      try {
        const response = await fetch(`/api/documents/${selectedTemplate}`);
        const data = await response.json();
        setHtmlTemplate(data.html);
        setJson(data.jsonData);
      } catch (error) {
        console.error('Erreur de chargement du document :', error);
      }
    };
    fetchDocumentContent();
  }, [selectedTemplate]);


  useEffect(() => {
    const eventSource = new EventSource('http://localhost:5000/stream');
    console.log('ÉTAPE 1 : Connexion au flux SSE…');

    eventSource.onmessage = event => {
      const updatedSection = JSON.parse(event.data);
      console.log('ÉTAPE 2 : Mise à jour reçue via SSE !', updatedSection);
      setJson(prev => ({ ...prev, ...updatedSection }));
    };

    eventSource.onerror = () => {
      console.error('Erreur de connexion SSE. Le flux a été fermé.');
      eventSource.close();
    };

    return () => {
      console.log('Fermeture de la connexion SSE.');
      eventSource.close();
    };
  }, []);

  // Effet #4 : régénère le HTML final à chaque changement de json ou htmlTemplate
  useEffect(() => {
    if (!htmlTemplate || !json) return;
    console.log('ÉTAPE 3 : Le JSON a changé, régénération du HTML…');
    const preparedHtmlContent = prepareHtml(htmlTemplate, json);
    setFichier(preparedHtmlContent);
  }, [json, htmlTemplate]);

  // --- 4. RENDU DU COMPOSANT ---
  return (
    <div className="app">
      <div className="main">
        <Header
          title="RFP"
          subtitle="Automatisez la création de votre RFP avec l’IA"
        />

        <div className="workspace">
          <div className="side-panel">
            <TemplateSelector
              templates={templates}
              selectedTemplate={selectedTemplate}
              setSelectedTemplate={setSelectedTemplate}
            />
          </div>

          <div className="content-panel">
            <DocumentPreview fichier={fichier} />
            <ChatWindow
              messages={messages}
              value={inputValue}
              onChange={setInputValue}
              onSend={handleSend}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
