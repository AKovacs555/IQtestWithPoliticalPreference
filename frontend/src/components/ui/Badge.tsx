import React from 'react';
import clsx from 'clsx';

const variants = {
  primary: 'gradient-primary text-white',
  outline: 'glass-card text-[var(--text)] border border-[var(--border)]',
};

export type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: keyof typeof variants;
};

const Badge = ({ variant = 'outline', className, ...props }: BadgeProps) => (
  <span
    className={clsx('inline-block px-2 py-1 rounded-full text-xs font-medium', variants[variant], className)}
    {...props}
  />
);

export default Badge;
