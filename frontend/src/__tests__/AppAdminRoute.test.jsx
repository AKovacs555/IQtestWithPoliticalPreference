import React from 'react';
import { describe, beforeEach, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';

let mockUser = null;
vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ user: mockUser, supabase: { auth: {} } }),
}));

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
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve([]) });
  });

  it('redirects non-admin users away from admin pages', async () => {
    const App = (await import('../pages/App.jsx')).default;
    mockUser = { id: '1', is_admin: false };
    render(
      <MemoryRouter initialEntries={['/admin/questions']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.queryByText(/Questions/i)).toBeNull();
  });

  it('allows admin users to access admin pages', async () => {
    const App = (await import('../pages/App.jsx')).default;
    mockUser = { id: '1', is_admin: true };
    render(
      <MemoryRouter initialEntries={['/admin/questions']}>
        <App />
      </MemoryRouter>
    );
    expect(await screen.findByText(/Import Questions/i)).toBeInTheDocument();
  });
});
