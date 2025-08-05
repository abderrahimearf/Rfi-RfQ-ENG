import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import './App.css';
import './App2.css';
import { useNavigate } from 'react-router-dom';
function Dashboard() {
  
  return (
    <div className="app">
          <div className="main">
            <Header
              title="RFP"
              subtitle="Automatisez la création de votre RFP avec l’IA"
            />
          </div>
     </div>
    
  );
}

export default Dashboard;
