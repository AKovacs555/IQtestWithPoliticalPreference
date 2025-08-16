import React from 'react';
import { signInWithGoogle } from '../lib/auth';
import Header from '../components/layout/Header';

export default function Login() {
  return (
    <>
      <Header />
      <div className="min-h-[calc(100dvh-80px)] flex flex-col items-center justify-center px-4">
        <p className="text-[var(--text-muted)] mb-6">Googleアカウントでログインが必要です</p>

        <div className="w-full max-w-xl gold-ring glass-surface p-6">
          <h2 className="text-lg font-bold mb-2">ログイン必須</h2>
          <p className="text-sm text-[var(--text-muted)] mb-5">
            IQ 2.0をご利用いただくにはGoogleアカウントでのログインが必要です
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
    </>
  );
}

