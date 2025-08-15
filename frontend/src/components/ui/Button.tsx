import React from 'react';
import clsx from 'clsx';

const base =
  'inline-flex items-center justify-center gap-2 font-medium rounded-md min-h-[44px] px-4 transition-transform duration-150 hover:-translate-y-px hover:scale-[1.01] active:translate-y-0 active:scale-95 focus-visible:ring-brand focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed';
const variants = {
  primary: 'gradient-primary text-white shadow-md hover:glow',
  outline: 'glass-card text-[var(--brand-cyan)]',
  ghost: 'text-[var(--text-muted)] hover:bg-[rgba(6,182,212,.08)]',
  destructive: 'bg-[var(--danger)] text-white hover:bg-red-600',
};

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants;
};

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', className, ...props }, ref) => (
    <button
      ref={ref}
      className={clsx(base, variants[variant], className)}
      {...props}
    />
  ),
);
Button.displayName = 'Button';

export default Button;
