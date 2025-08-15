import React from 'react';
import { Star } from 'lucide-react';

export default function GlobalRankCard({ rank }) {
  return (
    <div
      data-b-spec="card-rank"
      className="gold-card p-5 text-center space-y-2"
    >
      <div className="flex items-center justify-center gap-2">
        <Star className="w-5 h-5" style={{ color: '#FFD23F' }} />
        <div className="text-3xl md:text-4xl font-extrabold tracking-tight">#{rank}</div>
      </div>
      <span className="text-sm text-[var(--text)]/80">全体ランキング</span>
      <span className="inline-block mt-1 border border-[var(--gold-soft)] rounded-full px-2 py-0.5 text-xs text-[var(--text)]/80">
        Bronze
      </span>
    </div>
  );
}
