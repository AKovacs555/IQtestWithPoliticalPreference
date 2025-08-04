module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: 'var(--color-primary)',
        accent: 'var(--color-accent)',
        surface: 'var(--color-surface)',
        text: 'var(--color-text)',
      },
      dropShadow: {
        glow: [
          '0 0 8px rgba(58, 150, 250, 0.6)',
          '0 0 20px rgba(58, 150, 250, 0.4)',
        ],
      },
    },
  },
  plugins: [],
};
