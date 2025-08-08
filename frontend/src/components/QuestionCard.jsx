import React from 'react';
import QuestionCanvas from './QuestionCanvas';
import { OptionCard } from './OptionCard';

function getImageUrl(path) {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  const base = import.meta.env.VITE_SUPABASE_URL;
  return `${base}/storage/v1/object/public/iq-images/${path}`;
}

export default function QuestionCard({ question, onSelect, watermark, disabled = false }) {
  const { question: text, options, option_images = [] } = question;
  const qImg = getImageUrl(question.image);
  return (
    <div className="relative space-y-6 p-6 bg-white/70 dark:bg-slate-800/60 backdrop-blur-md rounded-2xl shadow-lg text-gray-900 dark:text-slate-100">
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20 text-xs select-none">
        {watermark}
      </div>
      {qImg && (
        <img
          src={qImg}
          loading="lazy"
          className="max-h-80 w-full object-contain mb-4"
          alt={question.image_prompt || 'question image'}
        />
      )}
      <QuestionCanvas question={text} options={[]} onSelect={onSelect} watermark={watermark} />
      <div className="space-y-3">
        {options.map((opt, i) => {
          const optImg = getImageUrl(option_images[i]);
          return (
            <OptionCard
              key={i}
              label={`${i + 1}. ${opt}`}
              imgSrc={optImg || undefined}
              selected={false}
              onClick={() => onSelect(i)}
              disabled={disabled}
            />
          );
        })}
      </div>
    </div>
  );
}
