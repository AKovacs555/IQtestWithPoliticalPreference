import React from 'react';
import ProgressBar from './ProgressBar';

export default function AdProgress({ progress }) {
  return (
    <div className="my-2" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
      <ProgressBar value={progress} />
    </div>
  );
}
