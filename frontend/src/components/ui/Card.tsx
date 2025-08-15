import React from 'react';
import clsx from 'clsx';

// basic glass card wrapper
export type CardProps = React.HTMLAttributes<HTMLDivElement>;

const Card = ({ className, ...props }: CardProps) => (
  <div className={clsx('glass-card p-4 md:p-6', className)} {...props} />
);

export default Card;
