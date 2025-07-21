import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import MobileOnlyWrapper from './MobileOnlyWrapper';
import './index.css';

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <MobileOnlyWrapper>
      <App />
    </MobileOnlyWrapper>
  </BrowserRouter>
);
