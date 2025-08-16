import React from 'react';
import { useLocation } from 'react-router-dom';
import { Brain } from 'lucide-react';

const Logo: React.FC = () => {
  const location = useLocation();
  const path = location.pathname;
  const isHomeOrLogin = path === '/' || path === '/login';

  return (
    <div className={`flex items-center ${isHomeOrLogin ? 'flex-col text-center' : ''}`}>
      <div
        className={`flex items-center justify-center ${isHomeOrLogin ? 'p-4 md:p-5' : 'p-2'} bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 rounded-full backdrop-blur-sm border border-cyan-400/30 glow-effect`}
      >
        <Brain className={`${isHomeOrLogin ? 'h-16 w-16 md:h-20 md:w-20' : 'h-10 w-10'} text-cyan-400`} />
      </div>
      <span
        className={`text-cyan-400 font-bold ${isHomeOrLogin ? 'mt-2 text-xl md:text-2xl' : 'ml-3 text-xl'}`}
      >
        IQ Clash
      </span>
    </div>
  );
};

export default Logo;

