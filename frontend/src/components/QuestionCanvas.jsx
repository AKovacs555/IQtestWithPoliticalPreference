import React from 'react';

// Rendering questions on a canvas discourages copy/paste and basic DOM scraping.
// It does not stop operating-system screenshots but adds a lightweight hurdle.

export default function QuestionCanvas({ question, options, onSelect, watermark }) {
  const ref = React.useRef(null);
  const [theme, setTheme] = React.useState(() => document.documentElement.getAttribute('data-theme'));

  React.useEffect(() => {
    const observer = new MutationObserver(() => {
      setTheme(document.documentElement.getAttribute('data-theme'));
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  React.useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = '16px sans-serif';
    const theme = document.documentElement.getAttribute('data-theme');
    ctx.fillStyle = theme === 'dark' ? '#fff' : '#000';
    ctx.fillText(question, 10, 20);
    options.forEach((opt, i) => {
      ctx.fillText(`${i + 1}. ${opt}`, 10, 50 + i * 24);
    });
    ctx.globalAlpha = 0.2;
    ctx.fillText(watermark, 10, canvas.height - 10);
    ctx.globalAlpha = 1;
  }, [question, options, watermark, theme]);

  const handleClick = (e) => {
    const y = e.nativeEvent.offsetY;
    const idx = Math.floor((y - 40) / 24);
    if (idx >= 0 && idx < options.length) onSelect(idx);
  };

  return <canvas ref={ref} width={300} height={200} onClick={handleClick} />;
}
