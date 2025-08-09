import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';

const signInWithOAuth = vi.fn();
vi.mock('../lib/supabase', () => ({
  supabase: { auth: { signInWithOAuth } },
}));

describe('google oauth button', () => {
  it('triggers signInWithOAuth with google provider', async () => {
    const LoginPage = (await import('../pages/LoginPage.jsx')).default;
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    const btn = screen.getByRole('button', { name: /google/i });
    fireEvent.click(btn);
    expect(signInWithOAuth).toHaveBeenCalledWith({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
  });
});
