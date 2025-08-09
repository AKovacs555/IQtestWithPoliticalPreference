import React from 'react';
import { describe, beforeEach, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';
import Navbar from '../components/Navbar';
import '../i18n';

function tokenFor(payload) {
  return `h.${btoa(JSON.stringify(payload))}.s`;
}

describe('Navbar admin link', () => {
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
  });

  it('hides admin link for non-admin users', () => {
    localStorage.setItem('authToken', tokenFor({ is_admin: false }));
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    expect(screen.queryByText(/Admin/i)).toBeNull();
  });

  it('shows admin link for admin users', () => {
    localStorage.setItem('authToken', tokenFor({ is_admin: true }));
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    expect(screen.getByText(/Admin/i)).toBeInTheDocument();
  });
});
