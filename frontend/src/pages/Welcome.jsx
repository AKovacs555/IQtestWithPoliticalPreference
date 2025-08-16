import React from 'react';
import { useSession } from '../hooks/useSession';
import { Link, useNavigate } from 'react-router-dom';

export default function Welcome() {
  const { signInWithGoogle } = useSession();
  const nav = useNavigate();
  return (
    <div className="min-h-[100dvh] center-stack px-4" data-b-spec="welcome-page">
      {/* big glow icon */}
      <div
        className="relative h-24 w-24 rounded-full flex items-center justify-center mb-2"
        style={{ boxShadow: '0 0 80px rgba(255,210,63,.25) inset, 0 0 60px rgba(255,210,63,.25)' }}
      >
        <span className="text-4xl">🧠</span>
      </div>
      {/* Title */}
      <h1 className="gradient-text-gold text-[36px] sm:text-[42px] font-extrabold tracking-tight">IQ Arena</h1>
      {/* Subtitle & subcaption */}
      <div className="space-y-1">
        <p className="text-[18px] sm:text-[20px] font-bold">IQで決着をつけよう</p>
        <p className="text-[var(--text-muted)] text-sm sm:text-base">あなたの知性を試す究極のプラットフォーム</p>
      </div>
      {/* CTAs */}
      <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-2">
        <button
          className="btn-cta w-full sm:w-auto"
          onClick={() => signInWithGoogle?.().catch(e => alert(e?.message || 'Sign-in failed'))}
        >
          <span>👤</span> アカウントを作成
        </button>
        <Link to="/login" className="btn-ghost w-full sm:w-auto">
          <span>🔑</span> ログイン
        </Link>
      </div>
    </div>
  );
}

