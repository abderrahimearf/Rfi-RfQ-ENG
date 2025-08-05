import React, { useState } from 'react';
import Header from './components/Header';
import Filter from './components/Filter';
import './App.css';
import './App2.css';

export default function App2() {
  const [titre, setTitre] = useState('');
  const [type,  setType]  = useState('');
  const [date,  setDate]  = useState('');

  return (
    <div className="app">
      <div className="main">
        <Header
          title="RFP"
          subtitle="Automatisez la création de votre RFP avec l’IA"
        />

       
        <Filter
          title={titre}
          onChangeTitle={setTitre}
          type={type}
          onChangeType={setType}
          date={date}
          onChangeDate={setDate}
        />

    
      </div>
    </div>
  );
}
