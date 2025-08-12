import React from 'react';
import { describe, beforeEach, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';

let mockUser = null;
vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ user: mockUser, loading: false, loaded: true }),
}));
vi.mock('../hooks/useSession', () => ({
  useSession: () => ({ user: mockUser, session: mockUser ? { user: mockUser } : null, loading: false, refresh: async () => {} }),
}));
vi.mock('../lib/auth', () => ({ signOut: vi.fn() }));
vi.mock('../pages/AuthCallback', () => ({ default: () => <div /> }));

describe('admin routes', () => {
  beforeEach(() => {
    localStorage.clear();
    window.matchMedia = window.matchMedia || (() => ({
      matches: false,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }));
    global.ResizeObserver = class {
      observe() {}
      disconnect() {}
    };
    import.meta.env.VITE_API_BASE = '';
    import.meta.env.VITE_SUPABASE_URL = 'http://localhost';
    import.meta.env.VITE_SUPABASE_ANON_KEY = 'anon';
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve([]) });
  });

  it('redirects non-admin users away from admin pages', async () => {
    const App = (await import('../pages/App.jsx')).default;
    mockUser = { id: '1', app_metadata: { is_admin: false } };
    render(
      <MemoryRouter initialEntries={['/admin/surveys']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.queryByText(/Surveys/i)).toBeNull();
  });

  it('allows admin users to access admin pages', async () => {
    const App = (await import('../pages/App.jsx')).default;
    mockUser = { id: '1', app_metadata: { is_admin: true } };
    render(
      <MemoryRouter initialEntries={['/admin/surveys']}>
        <App />
      </MemoryRouter>
    );
    expect(await screen.findByText(/New Survey/i)).toBeInTheDocument();
  });
});
