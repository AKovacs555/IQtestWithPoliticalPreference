import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, afterAll, test, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../hooks/useSession', () => ({
  useSession: () => ({ session: { access_token: 'token' } }),
}));

vi.mock('../lib/supabaseClient', () => ({
  supabase: {
    auth: { getUser: async () => ({ data: { user: { id: 'u1' } } }) },
    rpc: async () => ({ data: false, error: null }),
  },
}));

vi.mock('../lib/supabase/feed', () => ({
  fetchSurveyFeed: async () => [
    { id: 'i1', question_text: 'Q1', options: ['a', 'b'], group_id: 'g', lang: 'en', created_at: '', respondents: 0, answered_by_me: false },
    { id: 'i2', question_text: 'Q2', options: ['a', 'b'], group_id: 'g', lang: 'en', created_at: '', respondents: 0, answered_by_me: false },
  ],
  hasAnsweredToday: async () => false,
}));

vi.stubGlobal('fetch', (url: RequestInfo, opts?: RequestInit) => {
  if (typeof url === 'string' && url.includes('/surveys/answer')) {
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) }) as any;
  }
  return Promise.resolve({ ok: true, json: () => Promise.resolve({}) }) as any;
});

const DailySurvey = (await import('../pages/DailySurvey')).default;

afterAll(() => {
  (fetch as any).mockClear && (fetch as any).mockClear();
});

test('daily survey flow', async () => {
  localStorage.setItem('nationality', 'US');
  render(
    <MemoryRouter>
      <DailySurvey />
    </MemoryRouter>
  );
  expect(await screen.findByText('Q1')).toBeInTheDocument();
  fireEvent.click(screen.getByText('a'));
  expect(await screen.findByText('Q2')).toBeInTheDocument();
  fireEvent.click(screen.getByText('a'));
  expect(await screen.findByText('Daily 3 completed')).toBeInTheDocument();
  expect(screen.getByText('Start IQ test')).toBeInTheDocument();
});
