import React from 'react';
import { Trophy, Share2 } from 'lucide-react';

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
    <div
      data-b-spec="card-iq"
      className="gold-card p-5 text-center space-y-2"
    >
      <div className="flex items-center justify-center gap-2">
        <Trophy className="w-5 h-5" style={{ color: '#FFD23F' }} />
        <span className="font-semibold">現在のIQ</span>
      </div>
      <div className="text-4xl md:text-5xl font-extrabold">{score}</div>
      <button
        className="border border-[var(--gold-soft)] text-[var(--text)]/80 hover:bg-[rgba(255,224,130,.06)] h-11 px-5 rounded-md mx-auto flex items-center gap-2"
        onClick={share}
      >
        <Share2 className="w-4 h-4" />
        シェア
      </button>
    </div>
  );
}
