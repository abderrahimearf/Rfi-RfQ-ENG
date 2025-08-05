import React, { useState, useEffect } from 'react';
import compteIcon from '../compte1.png';
import { useNavigate } from 'react-router-dom';
// Composant pour l'effet machine à écrire
function AnimatedSubtitle({ text, speed = 100, pause = 1500 }) {
  const navigate = useNavigate();
  const [displayText, setDisplayText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    let timer;

    if (!isDeleting && index < text.length) {
      // Ajoute une lettre
      timer = setTimeout(() => {
        setDisplayText((prev) => prev + text.charAt(index));
        setIndex(index + 1);
      }, speed);
    } else if (isDeleting && index > 0) {
      // Supprime une lettre
      timer = setTimeout(() => {
        setDisplayText((prev) => prev.slice(0, -1));
        setIndex(index - 1);
      }, speed / 2);
    } else if (index === text.length && !isDeleting) {
      // Pause avant suppression
      timer = setTimeout(() => setIsDeleting(true), pause);
    } else if (index === 0 && isDeleting) {
      // Recommence
      setIsDeleting(false);
    }

    return () => clearTimeout(timer);
  }, [index, isDeleting, text, speed, pause]);

  return <p className="subtitle">{displayText}</p>;
}

export default function Header({ title, subtitle, newButtonText, onNew, onSearch }) {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (onSearch) onSearch(query); // Appelle la fonction passée en prop
  };

  return (
    <header className="header">
      {/* Sous-titre avec animation */}
      <div>
        <AnimatedSubtitle text={subtitle} />
      </div>

      {/* Barre de recherche */}
      <form className="search-bar" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Rechercher..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit"></button>
      </form>

      {}
      <div className="header-buttons">
        <button className="new-button" onClick={() => navigate('/Homme')}>Homme</button>
        <button className="new-button" onClick={() => navigate('/Dashboard')}>Dashboard</button>
        <button className="new-button" onClick={() => navigate('/')}>Templates</button>
        <button className="new-button" onClick={() => navigate('/data')}>DataBox</button>
        <button className="new-button">Settings</button>
      </div>
    </header>
  );
}
