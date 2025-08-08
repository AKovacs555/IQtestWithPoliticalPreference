import React from 'react';
import { describe, beforeEach, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';

// Helper to generate a fake JWT payload
function tokenFor(payload) {
  return `h.${btoa(JSON.stringify(payload))}.s`;
}

describe('admin routes', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubEnv('VITE_SHOW_ADMIN', 'true');
    window.matchMedia = window.matchMedia || (() => ({
      matches: false,
      addListener: () => {},
      removeListener: () => {}
    }));
  });

  it('redirects non-admin users away from admin pages', async () => {
    const App = (await import('../pages/App.jsx')).default;
    localStorage.setItem('authToken', tokenFor({ is_admin: false }));
    render(
      <MemoryRouter initialEntries={['/admin/questions']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.queryByText(/Questions/i)).toBeNull();
  });

  it('allows admin users to access admin pages', async () => {
    const App = (await import('../pages/App.jsx')).default;
    localStorage.setItem('authToken', tokenFor({ is_admin: true }));
    render(
      <MemoryRouter initialEntries={['/admin/questions']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText(/Questions/i)).toBeInTheDocument();
  });
});
