import React from 'react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <div className="navbar bg-base-100 shadow-md px-4">
      <div className="flex-1">
        <Link to="/" className="text-lg font-bold">IQ Test</Link>
      </div>
      <div className="flex-none gap-2">
        <Link to="/leaderboard" className="btn btn-ghost btn-sm">Leaderboard</Link>
        <Link to="/pricing" className="btn btn-ghost btn-sm">Pricing</Link>
        <Link to="/start" className="btn btn-primary btn-sm">Take Quiz</Link>
      </div>
    </div>
  );
}
