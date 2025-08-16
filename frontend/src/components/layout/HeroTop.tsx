import React from 'react';
import { Link } from 'react-router-dom';
import LanguageSelector from '../LanguageSelector';
import PointsBadge from '../PointsBadge';
import { useSession } from '../../hooks/useSession';

export default function HeroTop() {
  const { userId, isAdmin, logout } = useSession();
  return (
    <div className="hero-stack" data-b-spec="hero-top-with-logout">
      {/* Brand label removed; logo now lives in the global Header */}
      <p className="text-[12.5px] sm:text-sm text-[var(--text-muted)]">
        あなたのIQポテンシャルを解き放とう！
      </p>
      <div className="pills-row no-scrollbar flex-wrap justify-center w-full">
        <span className="pill">👑 <span>Bronze レベル</span></span>
        <PointsBadge userId={userId} className="pill" />
        <LanguageSelector className="pill" />
        {userId ? (
          <>
            <Link to="/profile" className="pill">
              👤 プロフィール
            </Link>
            <button
              type="button"
              onClick={logout}
              className="pill"
              data-b-spec="pill-logout"
            >
              🚪 ログアウト
            </button>
          </>
        ) : (
          <Link to="/login" className="pill">
            🔑 ログイン
          </Link>
        )}
        {isAdmin && (
          <Link to="/admin" className="pill">
            🛠 Admin
          </Link>
        )}
      </div>
    </div>
  );
}

