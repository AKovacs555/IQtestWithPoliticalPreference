import React from 'react';
import { Link } from 'react-router-dom';

export default function UpgradeTeaser() {
  return (
    <div className="glass-card p-6 text-center space-y-4 border border-[var(--brand-cyan)]/20">
      <h3 className="text-lg font-semibold">さらにIQ Arenaを楽しもう</h3>
      <p className="text-sm text-[var(--text-muted)]">
        Proになると受験が無制限になり、広告も最小限になります。
      </p>
      <Link
        to="/upgrade"
        className="gradient-primary text-white shadow-md hover:glow h-11 px-5 rounded-md inline-block"
      >
        アップグレード
      </Link>
    </div>
  );
}
