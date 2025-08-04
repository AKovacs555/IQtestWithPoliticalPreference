import React from 'react';
import usePersistedLang from '../hooks/usePersistedLang';
import Navbar from './Navbar';
import Footer from './Footer';

export default function Layout({ children }) {
  usePersistedLang();
  return (
    <div className="min-h-screen flex flex-col pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] text-gray-900 dark:text-slate-100">
      <Navbar />
      <main className="flex-1 w-full max-w-screen-sm mx-auto p-4 sm:p-8" role="main">
        {children}
      </main>
      <Footer />
    </div>
  );
}
