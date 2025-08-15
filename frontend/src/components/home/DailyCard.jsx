import React, { useEffect, useState } from 'react';
import { Brain } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Progress from '../ui/Progress';

export default function DailyCard({ count, onAnswerNext, onWatchAd, resetAt }) {
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

  return (
    <Card className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-[var(--brand-cyan)]" />
          <h2 className="font-semibold">今日のDaily 3</h2>
        </div>
        <span className="text-xs text-[var(--text-muted)]">リセットまで {timeLeft}</span>
      </div>
      <p className="text-sm text-[var(--text-muted)]">
        毎日3問に答えてIQテストを受けましょう
      </p>
      <div className="relative">
        <Progress value={(count / 3) * 100} className="h-3" />
        <span className="absolute inset-0 flex items-center justify-center text-xs font-medium">
          {count}/3 完了
        </span>
      </div>
      <div className="flex gap-3 pt-2">
        <Button className="flex-1 shine glow" onClick={onAnswerNext}>
          次の質問に答える
        </Button>
        <Button variant="outline" className="flex-1 ring-brand" onClick={onWatchAd}>
          広告を見て +1回
        </Button>
      </div>
    </Card>
  );
}
