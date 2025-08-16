import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Brain } from 'lucide-react';

type Variant = 'header' | 'hero';

export default function Logo({ variant = 'header' }: { variant?: Variant }) {
  const { pathname } = useLocation();
  const isLanding = pathname === '/' || pathname === '/login' || pathname === '/welcome';
  const v: Variant = variant === 'hero' || isLanding ? 'hero' : 'header';

  const iconSize = v === 'hero' ? 'h-16 w-16 md:h-20 md:w-20' : 'h-10 w-10';
  const textSize = v === 'hero' ? 'text-3xl md:text-4xl font-extrabold' : 'text-xl font-semibold';
  const dir = v === 'hero' ? 'flex-col text-center' : 'flex-row';

  const Icon = (
    <div className="p-4 bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 rounded-full backdrop-blur-sm border border-cyan-400/30 glow-effect">
      <Brain className={`${iconSize} text-cyan-400`} />
    </div>
  );

  const Label = <span className={`${textSize} text-cyan-400`}>IQ Clash</span>;

  return (
    <Link to="/" aria-label="Go to Home" className={`flex items-center ${dir} gap-2 select-none`} data-b-spec="logo">
      {Icon}
      {Label}
    </Link>
  );
}

