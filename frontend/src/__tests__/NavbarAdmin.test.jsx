import React from 'react';
import { describe, beforeEach, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';
import '../i18n';
import { vi } from 'vitest';

let mockUser = null;
vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ user: mockUser, loading: false }),
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
    Navbar = (await import('../components/Navbar')).default;
  });

  it('hides admin link for non-admin users', () => {
    mockUser = { id: '1', is_admin: false };
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    expect(screen.queryByText(/Admin/i)).toBeNull();
  });

  it('shows admin link for admin users', () => {
    mockUser = { id: '1', is_admin: true };
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    expect(screen.getByText(/Admin/i)).toBeInTheDocument();
  });
});
