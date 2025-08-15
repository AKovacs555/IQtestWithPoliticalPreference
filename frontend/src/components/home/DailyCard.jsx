import React, { useEffect, useState } from 'react';
import { Brain } from 'lucide-react';

export default function DailyCard({ count, onAnswerNext, onWatchAd, onStart, resetAt }) {
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    const tick = () => {
      const diff = resetAt.getTime() - new Date().getTime();
      const total = Math.max(0, Math.floor(diff / 1000));
      const h = String(Math.floor(total / 3600)).padStart(2, '0');
      const m = String(Math.floor((total % 3600) / 60)).padStart(2, '0');
      const s = String(total % 60).padStart(2, '0');
      setTimeLeft(`${h}:${m}:${s}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [resetAt]);

  const percent = (count / 3) * 100;
  const mainAction =
    count >= 3
      ? { label: 'IQテストを開始', onClick: onStart }
      : { label: '次の質問に答える', onClick: onAnswerNext };

  return (
    <div
      data-b-spec="card-daily"
      className="gold-card p-4 md:p-6 space-y-4 md:space-y-6"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-6 h-6" />
          <h2 className="text-lg md:text-xl font-semibold">今日のDaily 3</h2>
        </div>
        <span className="text-xs text-[var(--text-muted)]">リセットまで {timeLeft}</span>
      </div>
      <p className="text-sm text-[var(--text-muted)]">毎日3問に答えてIQテストを受けましょう</p>
      <div className="relative">
        <div className="thin-progress">
          <div className="bar" style={{ width: `${percent}%` }} />
        </div>
        <span className="absolute inset-0 flex items-center justify-center text-xs font-medium">
          {count}/3 完了
        </span>
      </div>
      <div className="flex gap-3 pt-1">
        <button
          className="gradient-primary text-white shadow-md hover:glow h-11 px-5 rounded-md flex-1"
          onClick={mainAction.onClick}
        >
          {mainAction.label}
        </button>
        <button
          className="border border-[var(--gold-soft)] text-[var(--text)]/80 hover:bg-[rgba(255,224,130,.06)] h-11 px-5 rounded-md flex-1"
          onClick={onWatchAd}
        >
          広告を見て +1回
        </button>
      </div>
    </div>
  );
}
