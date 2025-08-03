import React from 'react';

export default function ProgressBar({ value }) {
  return (
    <div
      className="h-2 rounded bg-gray-300 dark:bg-gray-700"
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="h-2 rounded bg-primary transition-all" style={{ width: `${value}%` }} />
    </div>
  );
}
