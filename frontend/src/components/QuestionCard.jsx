import React from 'react';
import QuestionCanvas from './QuestionCanvas';

export default function QuestionCard({ question, onSelect, watermark }) {
  const { question: text, options } = question;
  return (
    <div className="card bg-base-100 shadow-md p-4 space-y-4 relative">
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20 text-xs select-none">
        {watermark}
      </div>
      {question.image && (
        <img
          src={question.image}
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
      <div className="grid grid-cols-2 gap-2">
        {options.map((_, i) => (
          <button
            key={i}
            onClick={() => onSelect(i)}
            className="btn btn-primary"
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  );
}
