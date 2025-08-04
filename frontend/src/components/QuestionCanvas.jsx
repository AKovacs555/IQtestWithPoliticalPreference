import React from 'react';

// Rendering questions on a canvas discourages copy/paste and basic DOM scraping.
// It does not stop operating-system screenshots but adds a lightweight hurdle.

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(' ');
  let line = '';
  const lines = [];
  words.forEach((word) => {
    const testLine = line + word + ' ';
    const metrics = ctx.measureText ? ctx.measureText(testLine) : { width: testLine.length * 10 };
    if (metrics.width > maxWidth && line !== '') {
      lines.push(line.trim());
      line = word + ' ';
    } else {
      line = testLine;
    }
  });
  lines.push(line.trim());
  lines.forEach((l, i) => ctx.fillText(l, x, y + i * lineHeight));
  return lines.length;
}

export default function QuestionCanvas({ question, options, onSelect, watermark }) {
  const ref = React.useRef(null);
  const questionLinesRef = React.useRef(0);
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
    const maxWidth = canvas.width - 20;
    const questionLines = wrapText(ctx, question, 10, 20, maxWidth, 24);
    questionLinesRef.current = questionLines;
    const optionsStartY = 40 + questionLines * 24;
    options.forEach((opt, i) => {
      ctx.fillText(`${i + 1}. ${opt}`, 10, optionsStartY + i * 24);
    });
    ctx.globalAlpha = 0.2;
    ctx.fillText(watermark, 10, canvas.height - 10);
    ctx.globalAlpha = 1;
  }, [question, options, watermark, theme]);

  const handleClick = (e) => {
    const y = e.nativeEvent.offsetY;
    const optionsStartY = 40 + questionLinesRef.current * 24;
    const idx = Math.floor((y - optionsStartY) / 24);
    if (idx >= 0 && idx < options.length) onSelect(idx);
  };

  return <canvas ref={ref} width={300} height={260} onClick={handleClick} />;
}
