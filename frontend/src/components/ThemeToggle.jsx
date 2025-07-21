import React from 'react';

export default function ThemeToggle() {
  const [theme, setTheme] = React.useState(() => localStorage.getItem('theme') || 'pro');

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggle = () => setTheme(t => (t === 'pro' ? 'dark' : 'pro'));

  return (
    <button onClick={toggle} className="btn btn-ghost btn-sm">
      {theme === 'pro' ? 'Dark' : 'Light'} Mode
    </button>
  );
}
