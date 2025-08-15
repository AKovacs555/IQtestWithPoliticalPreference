import React from 'react';
import { Link } from 'react-router-dom';
import { signInWithGoogle } from '../lib/auth';

export default function Login() {
  return (
    <div className="min-h-[100dvh] flex flex-col items-center justify-center px-4">
      <div className="mb-6 w-full max-w-xl">
        <Link to="/" className="text-sm text-[var(--text-muted)] hover:underline inline-flex items-center gap-1">
          <span>←</span> ホームに戻る
        </Link>
      </div>

      <div className="h-14 w-14 rounded-full bg-cyan-500/20 text-cyan-300 flex items-center justify-center text-2xl mb-3">
        {'{ }'}
      </div>
      <h1 className="gradient-text-gold text-3xl font-extrabold mb-1">IQ Arena</h1>
      <p className="text-[var(--text-muted)] mb-6">Googleアカウントでログインが必要です</p>

      <div className="w-full max-w-xl gold-ring glass-surface p-6">
        <h2 className="text-lg font-bold mb-2">ログイン必須</h2>
        <p className="text-sm text-[var(--text-muted)] mb-5">
          IQ Arenaをご利用いただくにはGoogleアカウントでのログインが必要です
        </p>
        <button
          type="button"
          className="btn-google"
          onClick={() => signInWithGoogle().catch(err => alert(err?.message || 'Sign-in failed'))}
        >
          <span>🔄</span> Googleでログイン
        </button>
        <p className="mt-5 text-xs text-[var(--text-muted)] text-center leading-relaxed">
          ログインすることで、利用規約とプライバシーポリシーに同意したものとみなされます
        </p>
      </div>
    </div>
  );
}

