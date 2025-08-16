import React from 'react';
import { Link } from 'react-router-dom';
import PointsBadge from '../PointsBadge';
import LanguageSelector from '../LanguageSelector';
import { useSession } from '../../hooks/useSession';

export default function AdminHeroTop() {
  const { userId, logout } = useSession();
  return (
    <div className="hero-stack" data-b-spec="hero-admin-top">
      <h1
        className="float-slow gradient-text-gold"
        style={{ fontSize: 'clamp(28px,4vw,36px)', lineHeight: 1.15 }}
      >
        Admin
      </h1>
      <p className="text-[12.5px] sm:text-sm text-[var(--text-muted)]">管理ツール</p>
      <div className="pills-row no-scrollbar">
        <span className="pill">👑 <span>Bronze レベル</span></span>
        <PointsBadge userId={userId} className="pill" />
        <LanguageSelector className="pill" />
        <Link to="/profile" className="pill">👤 プロフィール</Link>
        <button
          type="button"
          onClick={logout}
          className="pill"
          data-b-spec="pill-logout"
        >
          🚪 ログアウト
        </button>
        <Link to="/admin" className="pill">🧭 ダッシュボード</Link>
      </div>
    </div>
  );
}

