import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { shareResult } from '../utils/share';
import '@testing-library/jest-dom/vitest';

describe('shareResult', () => {
  it('appends hashtags for navigator.share', async () => {
    const spy = vi.fn().mockResolvedValue(undefined);
    (navigator as any).share = spy;
    await shareResult({ text: 'test', url: 'https://x.test', hashtags: ['Tag'] });
    expect(spy).toHaveBeenCalledWith({ title: undefined, text: 'test #Tag', url: 'https://x.test' });
    delete (navigator as any).share;
  });

  it('falls back to twitter with hashtags', async () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null);
    await shareResult({ text: 'hi', url: 'https://x.test', hashtags: ['Tag'] });
    expect(open).toHaveBeenCalled();
    const url = open.mock.calls[0][0];
    expect(url).toContain('hashtags=Tag');
    open.mockRestore();
  });
});

import { render } from '@testing-library/react';
import useShareMeta from '../hooks/useShareMeta';

function MetaComp() {
  useShareMeta('http://example.com/img.png');
  return null;
}

describe('useShareMeta', () => {
  it('sets og:image meta tag', () => {
    render(<MetaComp />);
    const tag = document.querySelector('meta[property="og:image"]') as HTMLMetaElement;
    expect(tag).toBeTruthy();
    expect(tag.content).toBe('http://example.com/img.png');
  });
});
