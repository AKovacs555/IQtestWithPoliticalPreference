import React from 'react';
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import { ColorModeContext } from '../theme';

export default function ThemeToggle() {
  const { mode, setMode } = React.useContext(ColorModeContext);
  const toggle = () => setMode(mode === 'light' ? 'dark' : 'light');

  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-primary text-gray-900 dark:text-slate-100"
    >
      {mode === 'light' ? (
        <MoonIcon className="h-5 w-5" />
      ) : (
        <SunIcon className="h-5 w-5" />
      )}
    </button>
  );
}
