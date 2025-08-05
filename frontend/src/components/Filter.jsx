// src/components/Filter.jsx
import React from 'react';

const styles = {
  container: {
    width: '100%',                  // prend toute la largeur de son parent
    background: '#f0f0f0',          // fond clair
    padding: '16px',                // espace autour
    display: 'flex',
    alignItems: 'center',
    gap: '32px',                    // espace entre chaque champ
    boxSizing: 'border-box'
  },
  field: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  label: {
    fontSize: '1rem',
    fontWeight: 500
  },
  input: {
    width: '150px',
    height: '28px',
    background: '#d9534f',          // rouge vif comme sur ta maquette
    border: 'none',
    borderRadius: '4px'
  }
};

export default function Filter({
  title = '',
  type = '',
  date = '',
  onChangeTitle = () => {},
  onChangeType = () => {},
  onChangeDate = () => {}
}) {
  return (
    <div style={styles.container}>
      <div style={styles.field}>
        <span style={styles.label}>Titre</span>
        <input
          type="text"
          value={title}
          onChange={e => onChangeTitle(e.target.value)}
          style={styles.input}
        />
      </div>
      <div style={styles.field}>
        <span style={styles.label}>Type</span>
        <input
          type="text"
          value={type}
          onChange={e => onChangeType(e.target.value)}
          style={styles.input}
        />
      </div>
      <div style={styles.field}>
        <span style={styles.label}>Date</span>
        <input
          type="date"
          value={date}
          onChange={e => onChangeDate(e.target.value)}
          style={styles.input}
        />
      </div>
    </div>
  );
}
