import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './pages/App';
import MobileOnlyWrapper from './components/MobileOnlyWrapper';
import { SessionProvider } from './hooks/useSession';
import './styles.css';

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <SessionProvider>
      <MobileOnlyWrapper>
        <App />
      </MobileOnlyWrapper>
    </SessionProvider>
  </BrowserRouter>
);
