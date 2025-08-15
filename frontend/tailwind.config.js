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
          cyan: 'var(--brand-cyan)',
          emerald: 'var(--brand-emerald)',
        },
        text: 'var(--text)',
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
          backgroundImage: 'linear-gradient(90deg,var(--brand-cyan),var(--brand-emerald))',
        },
        '.gradient-text-gold': {
          backgroundImage: 'linear-gradient(120deg,#d4af37,#ffd700,#fff3b0)',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          color: 'transparent',
        },
        '.gold-ring': {
          border: '1px solid var(--gold-soft)',
          boxShadow:
            '0 0 0 1px rgba(255,224,130,.18) inset, 0 10px 28px var(--gold-glow), 0 2px 0 rgba(255,224,130,.10) inset',
          borderRadius: 'var(--radius-lg)',
        },
        '.gold-sheen': {
          position: 'relative',
          overflow: 'hidden',
        },
        '.gold-sheen::before': {
          content: '""',
          position: 'absolute',
          inset: '-1px',
          borderRadius: 'inherit',
          pointerEvents: 'none',
          background: 'radial-gradient(600px 300px at 0% 0%, rgba(255,216,96,.16), transparent 40%)',
        },
        '.gold-sheen::after': {
          content: '""',
          position: 'absolute',
          inset: '-30% -60%',
          borderRadius: 'inherit',
          pointerEvents: 'none',
          background:
            'linear-gradient(115deg, transparent 0%, rgba(255,255,255,.10) 22%, rgba(255,248,196,.22) 38%, transparent 62%)',
          animation: 'sheen-move 6s linear infinite',
        },
        '@keyframes sheen-move': {
          from: { transform: 'translateX(-60%)' },
          to: { transform: 'translateX(60%)' },
        },
        '.thin-progress': {
          height: '8px',
          borderRadius: '9999px',
          background: 'rgba(6,182,212,.20)',
          overflow: 'hidden',
        },
        '.thin-progress > .bar': {
          height: '100%',
          width: '0%',
          borderRadius: '9999px',
          backgroundImage: 'linear-gradient(90deg,#22d3ee,#10b981)',
          transition: 'width 250ms var(--ease)',
        },
      });
    }),
  ],
};
