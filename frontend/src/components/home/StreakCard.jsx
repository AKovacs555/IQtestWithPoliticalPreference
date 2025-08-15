import React from 'react';
import { Zap } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';

export default function StreakCard({ days }) {
  return (
    <Card className="text-center space-y-2">
      <div className="flex items-center justify-center gap-2">
        <Zap className="w-5 h-5 text-yellow-400" />
        <span className="font-semibold">連続日数</span>
      </div>
      <div className="text-3xl font-bold">{days}日</div>
      <Badge variant="primary">ストリーク継続中！</Badge>
    </Card>
  );
}
