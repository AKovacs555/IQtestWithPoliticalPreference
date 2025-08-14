import React from 'react';
import clsx from 'clsx';

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
}

const Progress = ({ value, className, ...props }: ProgressProps) => (
  <div
    className={clsx('w-full h-2 bg-[rgba(6,182,212,.20)] rounded-full overflow-hidden', className)}
    {...props}
  >
    <div
      className="h-full gradient-primary rounded-full transition-all duration-250"
      style={{ width: `${value}%` }}
    />
  </div>
);

export default Progress;
