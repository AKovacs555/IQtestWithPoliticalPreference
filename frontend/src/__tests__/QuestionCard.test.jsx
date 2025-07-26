import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect, beforeAll } from 'vitest';
import '@testing-library/jest-dom/vitest';
import QuestionCard from '../components/QuestionCard';

beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = () => ({
    clearRect: () => {},
    fillText: () => {},
    globalAlpha: 1,
  });
});

describe('QuestionCard', () => {
  it('renders four option buttons', () => {
    const q = { question: 'Q?', options: ['A','B','C','D'] };
    const { getAllByRole } = render(<QuestionCard question={q} onSelect={() => {}} />);
    const buttons = getAllByRole('button');
    expect(buttons).toHaveLength(4);
    expect(buttons[0]).toHaveTextContent('1');
    expect(buttons[3]).toHaveTextContent('4');
  });
});
