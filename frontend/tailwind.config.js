// tailwind theme for b-spec ui
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
      colors: {
        brand: {
          cyan: "var(--brand-cyan)",
          emerald: "var(--brand-emerald)",
          cyan600: "var(--brand-cyan-600)",
          emerald600: "var(--brand-emerald-600)",
        },
        text: "var(--text)",
        'text-muted': 'var(--text-muted)',
      },
    },
  },
  plugins: [
    require('tailwindcss/plugin')(function ({ addUtilities }) {
      addUtilities({
        '.glass-card': {
          background: 'var(--glass)',
          backdropFilter: 'blur(8px)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-card)',
        },
        '.gradient-primary': {
          backgroundImage: 'linear-gradient(90deg, var(--brand-cyan), var(--brand-emerald))',
        },
        '.ring-brand': {
          boxShadow: 'var(--ring)',
        },
        '.glow': {
          boxShadow: 'var(--shadow-glow)',
        },
      });
    }),
  ],
};
