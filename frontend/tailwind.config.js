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
          borderRadius: '16px',
          boxShadow: 'var(--shadow-card)',
        },
        /* dark glass background surface */
        '.card-glass': {
          background: 'rgba(15,23,42,.60)',
          backdropFilter: 'blur(8px)',
          borderRadius: '16px',
        },
        '.gradient-primary': {
          backgroundImage: 'linear-gradient(90deg,var(--brand-cyan),var(--brand-emerald))',
        },
        '.gradient-text-gold': {
          backgroundImage: 'linear-gradient(180deg,#FFE37A 0%,#F7C948 45%,#DEA300 100%)',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          color: 'transparent',
          textShadow: '0 2px 24px rgba(255,210,63,.25)',
        },
        '.bg-gradient-pro': {
          background: 'linear-gradient(90deg, #06b6d4, #059669)',
        },
        '.bg-pro-gradient': {
          background: 'linear-gradient(90deg,#06b6d4,#059669)',
        },
        '.bg-cta-gradient': {
          background: 'linear-gradient(90deg,#22d3ee,#10b981)',
        },
        /* gold ring + soft glow used on all cards/banners */
        '.gold-ring': {
          border: '1px solid rgba(255,224,130,.35)',
          borderRadius: '16px',
          boxShadow:
            '0 0 0 1px rgba(255,224,130,.18) inset, 0 10px 28px rgba(255,210,63,.22), 0 2px 0 rgba(255,224,130,.10) inset',
        },
        '.gold-sheen': { position: 'relative', overflow: 'hidden' },
        '.gold-sheen::before': {
          content: "\"\"",
          position: 'absolute',
          inset: '-1px',
          borderRadius: 'inherit',
          pointerEvents: 'none',
          background: 'radial-gradient(600px 300px at 0% 0%, rgba(255,216,96,.16), transparent 40%)',
        },
        '.gold-sheen::after': {
          content: "\"\"",
          position: 'absolute',
          inset: '-40% -80%',
          borderRadius: 'inherit',
          pointerEvents: 'none',
          background:
            'linear-gradient(115deg, transparent 0%, rgba(255,255,255,.12) 18%, rgba(255,248,196,.22) 32%, transparent 50%)',
          animation: 'sheen-move 6s linear infinite',
          WebkitMaskImage:
            'radial-gradient(200% 100% at 50% 50%, #000 60%, transparent 80%)',
          maskImage:
            'radial-gradient(200% 100% at 50% 50%, #000 60%, transparent 80%)',
        },
        '@keyframes sheen-move': {
          '0%': { transform: 'translateX(-66%)' },
          '100%': { transform: 'translateX(66%)' },
        },
        /* progress bar */
        '.progress-track': {
          height: '8px',
          width: '100%',
          borderRadius: '9999px',
          background: 'rgba(6,182,212,.18)',
          overflow: 'hidden',
        },
        '.progress-bar': {
          height: '100%',
          width: '0%',
          borderRadius: '9999px',
          backgroundImage: 'linear-gradient(90deg,#22d3ee,#10b981)',
          transition: 'width .25s cubic-bezier(.22,.61,.36,1)',
        },
        '.bg-gradient-gold': {
          background: 'radial-gradient(circle at center, var(--gold-soft), transparent 80%), var(--bg-900)',
        },
        '.shadow-gold': {
          boxShadow: 'var(--shadow-glow)',
        },
        '.btn-primary': {
          background: '#10b981',
          color: 'white',
          fontWeight: '700',
          borderRadius: '12px',
          padding: '0 20px',
          height: '44px',
          boxShadow: '0 0 0 0 rgba(16,185,129,0)',
          transition: 'box-shadow .2s ease, transform .15s ease',
        },
        '.btn-primary:hover': {
          boxShadow: '0 8px 24px rgba(16,185,129,.45)',
          transform: 'translateY(-1px) scale(1.01)',
        },
        '.btn-outline': {
          border: '1px solid rgba(148,163,184,.25)',
          color: 'var(--text)',
          borderRadius: '12px',
          padding: '0 16px',
          height: '44px',
        },
        /* layout helpers */
        '.banner-wrap': {
          borderRadius: '16px',
          padding: '20px',
        },
        '.no-tabs-header': {
          position: 'sticky',
          top: '0',
          zIndex: '50',
          backdropFilter: 'blur(8px)',
          background: 'rgba(15,23,42,.60)',
          borderBottom: '1px solid rgba(148,163,184,.12)',
        },
        '.gold-card': { '@apply card-glass gold-ring gold-sheen': {} },
        /* hero stack and pills */
        '.hero-stack': {
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: '10px',
          paddingTop: '14px',
          paddingBottom: '6px',
        },
        '.pills-row': {
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          overflowX: 'auto',
          padding: '2px 4px',
        },
        '.pill': {
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          height: '32px',
          padding: '0 12px',
          borderRadius: '9999px',
          border: '1px solid rgba(148,163,184,.18)',
          background: 'rgba(11,17,32,.55)',
          color: '#E2E8F0',
          whiteSpace: 'nowrap',
        },
        '.pill:hover': {
          background: 'rgba(255,200,0,.10)',
        },
        '.no-scrollbar': {
          scrollbarWidth: 'none',
          MsOverflowStyle: 'none',
        },
        '.no-scrollbar::-webkit-scrollbar': { display: 'none' },
        /* floating logo */
        '@keyframes float-slow': {
          '0%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-2px)' },
          '100%': { transform: 'translateY(0)' },
        },
        '.float-slow': { animation: 'float-slow 6s ease-in-out infinite' },
        /* glass surface */
        '.glass-surface': {
          background: 'rgba(15,23,42,.60)',
          backdropFilter: 'blur(8px)',
          borderBottom: '1px solid rgba(148,163,184,.12)',
        },
        /* google login button */
        '.btn-google': {
          background: '#FFFFFF',
          color: '#0B0F1F',
          height: '48px',
          borderRadius: '9999px',
          padding: '0 16px',
          fontWeight: '700',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px',
          width: '100%',
          boxShadow: '0 6px 16px rgba(0,0,0,.18)',
          transition: 'transform .15s ease, box-shadow .15s ease',
        },
        '.btn-google:hover': {
          transform: 'translateY(-1px)',
          boxShadow: '0 10px 28px rgba(0,0,0,.28)',
        },
      });
    }),
  ],
};
