import React from 'react';
import { Trophy, Share2 } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';

export default function CurrentIQCard({ score }) {
  const share = () => {
    const text = `I scored ${score} IQ on IQ Arena! #IQArena`;
    if (navigator.share) {
      navigator.share({ text });
    } else {
      window.open(
        `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`,
        '_blank'
      );
    }
  };

  return (
    <Card className="text-center space-y-2">
      <div className="flex items-center justify-center gap-2">
        <Trophy className="w-5 h-5 text-yellow-500" />
        <span className="font-semibold">現在のIQ</span>
      </div>
      <div className="text-3xl font-bold">{score}</div>
      <Button variant="outline" className="mx-auto ring-brand" onClick={share}>
        <Share2 className="w-4 h-4" />
        シェア
      </Button>
    </Card>
  );
}
