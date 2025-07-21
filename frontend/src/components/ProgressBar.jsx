import React from 'react';

export default function ProgressBar({ value }) {
  return (
    <div className="h-2 bg-base-200 rounded">
      <div className="h-2 bg-primary rounded" style={{ width: `${value}%` }} />
    </div>
  );
}
