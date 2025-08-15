import React from 'react';
import { Star } from 'lucide-react';
import Card from '../ui/Card';

export default function GlobalRankCard({ rank }) {
  return (
    <Card className="text-center space-y-2">
      <div className="flex items-center justify-center gap-2">
        <Star className="w-5 h-5 text-orange-400" />
        <span className="font-semibold">世界ランク</span>
      </div>
      <div className="text-3xl font-bold">#{rank}</div>
      <span className="text-sm text-amber-700">Bronze</span>
    </Card>
  );
}
