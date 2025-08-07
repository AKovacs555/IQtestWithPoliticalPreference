import React from 'react';
import { describe, beforeEach, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../pages/App.jsx';
import '@testing-library/jest-dom/vitest';

// Helper to generate a fake JWT payload
function tokenFor(payload) {
  return `h.${btoa(JSON.stringify(payload))}.s`;
}

describe('admin routes', () => {
  beforeEach(() => {
    localStorage.clear();
    // ensure admin pages are included in build
    process.env.VITE_SHOW_ADMIN = 'true';
    // jsdom lacks matchMedia; provide a basic stub
    window.matchMedia = window.matchMedia || (() => ({
      matches: false,
      addListener: () => {},
      removeListener: () => {}
    }));
    // non-admin user token
    localStorage.setItem('authToken', tokenFor({ is_admin: false }));
  });

  it('renders admin pages without authentication', () => {
    render(
      <MemoryRouter initialEntries={['/admin/questions']}>
        <App />
      </MemoryRouter>
    );
    expect(screen.queryByText(/Admin access required/i)).toBeNull();
  });
});
