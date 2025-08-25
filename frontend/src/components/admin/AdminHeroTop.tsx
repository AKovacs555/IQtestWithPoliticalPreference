import React from 'react';
import { Link } from 'react-router-dom';
import LanguageSelector from '../LanguageSelector';
import { useSession } from '../../hooks/useSession';
import { supabase } from '../../lib/supabaseClient';
import { refreshAnalytics } from '../../lib/supabase/analytics';

export default function AdminHeroTop() {
  const { userId, logout, isAdmin } = useSession();

  const onRefreshAnalytics = async () => {
    try {
      await refreshAnalytics(supabase);
      if (window?.toast) window.toast('Analytics refreshed');
    } catch (e) {
      console.error(e);
      if (window?.toast) window.toast('Failed to refresh analytics');
    }
  };
  return (
    <div className="hero-stack" data-b-spec="hero-admin-top">
      <h1
        className="float-slow gradient-text-gold"
        style={{ fontSize: 'clamp(28px,4vw,36px)', lineHeight: 1.15 }}
      >
        Admin
      </h1>
      <p className="text-[12.5px] sm:text-sm text-[var(--text-muted)]">管理ツール</p>
      <div className="pills-row no-scrollbar flex-wrap justify-center sm:justify-start">
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
        {isAdmin && (
          <button
            type="button"
            onClick={onRefreshAnalytics}
            className="pill"
            data-b-spec="pill-refresh-analytics"
          >
            🔄 Refresh analytics
          </button>
        )}
      </div>
    </div>
  );
}

