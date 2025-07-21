import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import ProgressBar from '../components/ProgressBar';

describe('ProgressBar', () => {
it('renders with width style', () => {
  const { getByRole } = render(<ProgressBar value={50} />);
  const bar = getByRole('progressbar').firstChild;
  expect(bar).toHaveStyle('width: 50%');
});
});
