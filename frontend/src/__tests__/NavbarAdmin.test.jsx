import React from 'react';
import { describe, beforeEach, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';
import '../i18n';

let mockUser = null;
let mockIsAdmin = false;
vi.mock('../hooks/useSession', () => ({
  useSession: () => ({
    user: mockUser,
    userId: mockUser?.id ?? null,
    isAdmin: mockIsAdmin,
    loading: false,
    refresh: async () => {},
  }),
}));
vi.mock('../lib/auth', () => ({ signOut: vi.fn(), signInWithGoogle: vi.fn() }));

let Navbar;

describe('Navbar admin link', () => {
  beforeEach(async () => {
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
    import.meta.env.VITE_SUPABASE_URL = 'http://localhost';
    import.meta.env.VITE_SUPABASE_ANON_KEY = 'anon';
    Navbar = (await import('../components/Navbar')).default;
  });

  it('hides admin link for non-admin users', () => {
    mockUser = { id: '1' };
    mockIsAdmin = false;
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    expect(screen.queryByText(/Admin/i)).toBeNull();
  });

  it('shows admin link for admin users', () => {
    mockUser = { id: '1' };
    mockIsAdmin = true;
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    const link = screen.getByRole('link', { name: /Admin/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/admin');
  });
});
