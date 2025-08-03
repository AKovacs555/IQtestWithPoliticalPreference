import React from 'react';
import { Link } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';
import PointsBadge from './PointsBadge';
import LanguageSelector from './LanguageSelector';

export default function Navbar() {
  const userId = 'demo';
  // Show Admin link if VITE_SHOW_ADMIN === 'true'  (set in Vercel env vars)
  const showAdmin = import.meta.env.VITE_SHOW_ADMIN === 'true' || import.meta.env.DEV;
  return (
    <div className="navbar bg-base-100 shadow-md px-4">
      <div className="flex-1">
        <Link to="/" className="text-lg font-bold">IQ Test</Link>
      </div>
      <div className="flex-none gap-2">
        <ThemeToggle />
        <LanguageSelector />
        <PointsBadge userId={userId} />
        <Link to="/leaderboard" className="btn btn-ghost btn-sm">Leaderboard</Link>
        <Link to="/dashboard" className="btn btn-ghost btn-sm">Dashboard</Link>
        <Link to="/pricing" className="btn btn-ghost btn-sm">Pricing</Link>
        <Link to="/select-nationality" className="btn btn-ghost btn-sm">Nationality</Link>
        <Link to="/select-party" className="btn btn-ghost btn-sm">Parties</Link>
        <Link to="/test" className="btn btn-primary btn-sm">Take Quiz</Link>
        {showAdmin && (
          <>
            <Link to="/admin/upload" className="btn btn-ghost btn-sm">Upload</Link>
            <Link to="/admin/questions" className="btn btn-ghost btn-sm">Questions</Link>
          </>
        )}
      </div>
    </div>
  );
}
