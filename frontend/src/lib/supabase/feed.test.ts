import { describe, expect, test } from 'vitest';
import {
  creditPoints,
  fetchSurveyFeed,
  hasAnsweredToday,
  spendPoint,
} from './feed';

describe('feed rpc helpers', () => {
  test('fetchSurveyFeed returns data', async () => {
    const client = {
      rpc: async (_fn: string, _args: any) => ({
        data: [{
          id: '1',
          group_id: 'g',
          question_text: 'Q',
          options: [],
          lang: 'en',
          created_at: '',
          respondents: 0,
          answered_by_me: false,
        }],
        error: null,
      }),
    } as any;
    const rows = await fetchSurveyFeed(client, 'en', 50, 0);
    expect(rows.length).toBe(1);
    expect(rows[0].question_text).toBe('Q');
  });

  test('fetchSurveyFeed throws on error', async () => {
    const client = {
      rpc: async () => ({ data: null, error: new Error('boom') }),
    } as any;
    await expect(fetchSurveyFeed(client, 'en')).rejects.toThrow('boom');
  });

  test('hasAnsweredToday returns boolean', async () => {
    const client = { rpc: async () => ({ data: true, error: null }) } as any;
    const ok = await hasAnsweredToday(client);
    expect(ok).toBe(true);
  });

  test('hasAnsweredToday throws on error', async () => {
    const client = { rpc: async () => ({ data: null, error: new Error('e') }) } as any;
    await expect(hasAnsweredToday(client)).rejects.toThrow('e');
  });

  test('creditPoints throws on error', async () => {
    const client = { rpc: async () => ({ error: new Error('c') }) } as any;
    await expect(
      creditPoints(client, 'u', 1, 'reason', {})
    ).rejects.toThrow('c');
  });

  test('spendPoint returns boolean', async () => {
    const client = {
      rpc: async () => ({ data: true, error: null }),
    } as any;
    const ok = await spendPoint(client, 'u', 'reason', {});
    expect(ok).toBe(true);
  });

  test('spendPoint throws on error', async () => {
    const client = {
      rpc: async () => ({ data: null, error: new Error('s') }),
    } as any;
    await expect(spendPoint(client, 'u', 'r', {})).rejects.toThrow('s');
  });
});
