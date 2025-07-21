import React from 'react';
import { Link } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';

export default function Navbar() {
  return (
    <div className="navbar bg-base-100 shadow-md px-4">
      <div className="flex-1">
        <Link to="/" className="text-lg font-bold">IQ Test</Link>
      </div>
      <div className="flex-none gap-2">
        <ThemeToggle />
        <Link to="/leaderboard" className="btn btn-ghost btn-sm">Leaderboard</Link>
        <Link to="/pricing" className="btn btn-ghost btn-sm">Pricing</Link>
        <Link to="/select-set" className="btn btn-primary btn-sm">Take Quiz</Link>
      </div>
    </div>
  );
}
