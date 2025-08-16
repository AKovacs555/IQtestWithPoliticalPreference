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
      <div className="gold-ring glass-surface p-4 md:p-5">
        <p className="text-base sm:text-lg font-semibold">{item.body}</p>
      </div>
      <div className="space-y-3 md:space-y-4">
        {item.choices.map((c, idx) => (
          <button
            key={idx}
            type="button"
            className="choice"
            onClick={() => onAnswer(idx)}
            data-b-spec="survey-option"
          >
            <span className="choice__radio" />
            <span className="text-[15px] sm:text-base leading-6">{c}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
