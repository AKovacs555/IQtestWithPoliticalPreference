import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import DailySurvey from '../pages/DailySurvey';
import { vi, afterAll, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../hooks/useSession', () => ({
  useSession: () => ({ session: { access_token: 'token' } }),
}));

vi.stubGlobal('fetch', (url: RequestInfo, opts?: RequestInit) => {
  if (typeof url === 'string' && url.includes('/surveys/daily3')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ items: [{ id: 'i1', body: 'Q1', choices: ['a', 'b'] }, { id: 'i2', body: 'Q2', choices: ['a', 'b'] }] })
    }) as any;
  }
  if (typeof url === 'string' && url.includes('/surveys/answer')) {
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) }) as any;
  }
  return Promise.resolve({ ok: true, json: () => Promise.resolve({}) }) as any;
});

afterAll(() => {
  (fetch as any).mockClear && (fetch as any).mockClear();
});

test('daily survey flow', async () => {
  render(<DailySurvey />);
  expect(await screen.findByText('Q1')).toBeInTheDocument();
  fireEvent.click(screen.getByText('a'));
  expect(await screen.findByText('Q2')).toBeInTheDocument();
  fireEvent.click(screen.getByText('a'));
  expect(await screen.findByText('Daily 3 completed')).toBeInTheDocument();
  expect(screen.getByText('Start IQ test')).toBeInTheDocument();
});
