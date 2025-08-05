import React from 'react';
import { Sidebarh } from './components/sidebarh';
import { MainContent } from './components/main-content';
import { useNavigate } from 'react-router-dom';

const styles = {
  container: {
    display: 'flex',
    minHeight: '100vh',
   background: 'linear-gradient(to right, #7396dd, #b3b7b5)',

  }
};

export default function Homm() {
  const handleGetStarted = (type) =>
    console.log(`Starting ${type} generation...`);

  return (
    <div style={styles.container}>
      <Sidebarh />
      <MainContent onGetStarted={handleGetStarted} />
    </div>
  );
}
