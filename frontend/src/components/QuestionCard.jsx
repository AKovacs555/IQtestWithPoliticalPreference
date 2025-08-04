import React from 'react';
import QuestionCanvas from './QuestionCanvas';

export default function QuestionCard({ question, onSelect, watermark }) {
  const { question: text, options } = question;
  return (
    <div className="relative space-y-6 p-6 bg-white/70 backdrop-blur-md rounded-2xl shadow-lg">
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20 text-xs select-none">
        {watermark}
      </div>
      {question.image && (
        <img
          src={question.image}
          loading="lazy"
          className="max-h-80 w-full object-contain mb-4"
          alt={question.image_prompt || 'question image'}
        />
      )}
      <QuestionCanvas
        question={text}
        options={options}
        onSelect={onSelect}
        watermark={watermark}
      />
      <div className="grid grid-cols-2 gap-4">
        {options.map((_, i) => (
          <button
            key={i}
            onClick={() => onSelect(i)}
            className="w-full py-3 rounded-md bg-primary text-white hover:bg-blue-600 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  );
}
