import React from 'react';
import { Zap } from 'lucide-react';

export default function StreakCard({ days }) {
  return (
    <div
      data-b-spec="card-streak"
      className="gold-card p-5 text-center space-y-2"
    >
      <div className="flex items-center justify-center gap-2">
        <Zap className="w-5 h-5" style={{ color: '#FFD23F' }} />
        <span className="font-semibold">連続達成</span>
      </div>
      <div className="text-3xl md:text-4xl font-extrabold tracking-tight">{days}日</div>
      {days > 0 && (
        <span className="inline-block rounded-full text-xs px-2 py-1 gradient-primary text-white">
          ストリーク継続中！
        </span>
      )}
    </div>
  );
}
