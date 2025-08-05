import React from 'react';
import { Routes, Route } from 'react-router-dom';
import App from './App';   // page d'accueil
import App2 from './App2'; // autre page
import Homme from './homme';
import Dashboard from './dashboard';

const Ro = () => (
  <Routes>
    <Route path="/generation"     element={<App />} />
    <Route path="/data" element={<App2 />} />
    <Route path="/Homme" element={<Homme />} />
    <Route path="/Dashboard" element={<Dashboard />} />

  </Routes>
);

export default Ro;
