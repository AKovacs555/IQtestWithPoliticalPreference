import React from 'react';
import { render, fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, test, expect } from 'vitest';

vi.mock('../../hooks/useSession', () => ({
  useSession: () => ({ user: { id: 'u1' }, session: null }),
}));

const navigate = vi.fn();
const stateData = {
  survey: { id: 's1', group_id: 'g1', lang: 'en', is_single_choice: true, title: 't' },
  items: [{ id: 'i1', body: 'A', is_exclusive: false, position: 0 }],
};

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigate,
    useLocation: () => ({ state: stateData }),
  };
});

import Survey from '../Survey.jsx';

test('does not navigate on submit failure', async () => {
  global.fetch = vi.fn(() =>
    Promise.resolve({ ok: false, text: () => Promise.resolve('err') }),
  );

  const { container } = render(
    <MemoryRouter>
      <Survey />
    </MemoryRouter>,
  );

  fireEvent.click(screen.getByText('A'));
  fireEvent.click(container.querySelector('.btn-cta'));

  await waitFor(() => {
    expect(navigate).not.toHaveBeenCalled();
  });
  expect(screen.getByText('err')).toBeTruthy();
});
