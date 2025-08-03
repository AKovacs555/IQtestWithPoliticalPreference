import React from 'react';
import usePersistedLang from '../hooks/usePersistedLang';
import Navbar from './Navbar';
import Footer from './Footer';

export default function Layout({ children }) {
  usePersistedLang();
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 w-full max-w-screen-lg mx-auto px-4" role="main">
        {children}
      </main>
      <Footer />
    </div>
  );
}
