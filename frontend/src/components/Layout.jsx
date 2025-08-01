import React from 'react';
import usePersistedLang from '../hooks/usePersistedLang';
import Navbar from './Navbar';
import Footer from './Footer';

export default function Layout({ children }) {
  usePersistedLang();
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 container mx-auto p-4">{children}</main>
      <Footer />
    </div>
  );
}
