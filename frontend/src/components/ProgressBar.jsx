import React from 'react';

export default function ProgressBar({ value }) {
  return (
    <div className="h-2 bg-base-200 rounded" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
      <div className="h-2 bg-primary rounded" style={{ width: `${value}%` }} />
    </div>
  );
}
