import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';

const signInWithGoogle = vi.fn().mockResolvedValue(undefined);
vi.mock('../lib/auth', () => ({
  signInWithGoogle,
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
    expect(signInWithGoogle).toHaveBeenCalled();
  });
});
