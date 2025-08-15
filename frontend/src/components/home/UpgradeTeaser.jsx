import React from 'react';
import { Link } from 'react-router-dom';

export default function UpgradeTeaser() {
  return (
    <div className="glass-card p-6 text-center space-y-4">
      <h3 className="text-lg font-semibold">さらにIQ Arenaを楽しもう</h3>
      <p className="text-sm text-[var(--text-muted)]">
        Proになると受験が無制限になり、広告も最小限になります。
      </p>
      <Link
        to="/upgrade"
        className="inline-block px-4 py-2 rounded-md gradient-primary text-white shine glow ring-brand"
      >
        アップグレード
      </Link>
    </div>
  );
}
