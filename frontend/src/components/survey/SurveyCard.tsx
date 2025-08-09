import React from 'react';

interface Item {
  id: string;
  body: string;
  choices: string[];
}

interface Props {
  item: Item;
  onAnswer: (index: number) => void;
}

export default function SurveyCard({ item, onAnswer }: Props) {
  return (
    <div className="space-y-4">
      <p className="text-lg">{item.body}</p>
      <div className="space-y-2">
        {item.choices.map((c, idx) => (
          <button
            key={idx}
            className="w-full rounded bg-[var(--btn-primary)] text-white px-4 py-2 min-h-[44px]"
            onClick={() => onAnswer(idx)}
          >
            {c}
          </button>
        ))}
      </div>
    </div>
  );
}
