import React from 'react';
import clsx from 'clsx';

// basic glass card wrapper
export type CardProps = React.HTMLAttributes<HTMLDivElement>;

const Card = ({ className, ...props }: CardProps) => (
  <div className={clsx('glass-card p-4', className)} {...props} />
);

export default Card;
