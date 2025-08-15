import React from 'react';
import QuestionCanvas from './QuestionCanvas';
import Button from './ui/Button';
import Card from './ui/Card';

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
    <Card className="relative space-y-4">
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
            <Button
              key={i}
              variant="outline"
              disabled={disabled}
              onClick={() => onSelect(i)}
              className="w-full justify-start gap-3 group"
            >
              <span className="w-6 h-6 rounded-full border-2 border-[var(--border)] flex items-center justify-center">
                <span className="w-3 h-3 rounded-full bg-[var(--brand-cyan)] opacity-0 group-active:opacity-100" />
              </span>
              {optImg && <img src={optImg} alt="" className="max-h-10" />}
              <span className="flex-1 text-left">{opt}</span>
            </Button>
          );
        })}
      </div>
    </Card>
  );
}
