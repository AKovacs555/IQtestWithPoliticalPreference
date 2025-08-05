import React from 'react';

// Rendering questions on a canvas discourages copy/paste and basic DOM scraping.
// It does not stop operating-system screenshots but adds a lightweight hurdle.

function getWrappedLines(ctx, text, maxWidth) {
  const chars = Array.from(text);
  let line = '';
  const lines = [];
  chars.forEach((ch) => {
    if (ch === '\n') {
      lines.push(line);
      line = '';
      return;
    }
    const testLine = line + ch;
    const metrics = ctx.measureText ? ctx.measureText(testLine) : { width: testLine.length * 10 };
    if (metrics.width > maxWidth && line !== '') {
      lines.push(line);
      line = ch;
    } else {
      line = testLine;
    }
  });
  if (line) lines.push(line);
  return lines;
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
    ctx.font = '16px sans-serif';
    const theme = document.documentElement.getAttribute('data-theme');
    ctx.fillStyle = theme === 'dark' ? '#fff' : '#000';
    const maxWidth = canvas.width - 20;
    const lineHeight = 24;
    const questionLines = getWrappedLines(ctx, question, maxWidth);
    const optionsStartY = 20 + questionLines.length * lineHeight + 20;
    const neededHeight = optionsStartY + options.length * lineHeight + 20;
    if (canvas.height !== neededHeight) {
      canvas.height = neededHeight;
      ctx.font = '16px sans-serif';
      ctx.fillStyle = theme === 'dark' ? '#fff' : '#000';
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    questionLines.forEach((l, i) => ctx.fillText(l, 10, 20 + i * lineHeight));
    options.forEach((opt, i) => {
      ctx.fillText(`${i + 1}. ${opt}`, 10, optionsStartY + i * lineHeight);
    });
    ctx.globalAlpha = 0.2;
    ctx.fillText(watermark, 10, canvas.height - 10);
    ctx.globalAlpha = 1;
    questionLinesRef.current = questionLines.length;
  }, [question, options, watermark, theme]);

  const handleClick = (e) => {
    const y = e.nativeEvent.offsetY;
    const lineHeight = 24;
    const optionsStartY = 20 + questionLinesRef.current * lineHeight + 20;
    const idx = Math.floor((y - optionsStartY) / lineHeight);
    if (idx >= 0 && idx < options.length) onSelect(idx);
  };

  return <canvas ref={ref} width={300} height={260} onClick={handleClick} />;
}
