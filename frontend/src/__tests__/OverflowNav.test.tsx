import React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import OverflowNav from '../components/nav/OverflowNav';
import '@testing-library/jest-dom/vitest';

declare global {
  // eslint-disable-next-line no-var
  var ResizeObserver: any;
}

class RO {
  callback: ResizeObserverCallback;
  constructor(cb: ResizeObserverCallback) {
    this.callback = cb;
  }
  observe() {
    setTimeout(() => this.callback([], this), 0);
  }
  disconnect() {}
}

beforeEach(() => {
  global.ResizeObserver = RO;
});

it('renders link when space allows', async () => {
  Object.defineProperty(HTMLDivElement.prototype, 'clientWidth', { configurable: true, value: 1000 });
  Object.defineProperty(HTMLButtonElement.prototype, 'offsetWidth', { configurable: true, value: 100 });
  Object.defineProperty(HTMLAnchorElement.prototype, 'offsetWidth', { configurable: true, value: 100 });

  render(
    <MemoryRouter>
      <OverflowNav items={[{ label: 'Questions', href: '/admin/questions' }]} />
    </MemoryRouter>,
  );

  const link = await screen.findByRole('link', { name: 'Questions' });
  expect(link).toHaveAttribute('href', '/admin/questions');
});

it('renders overflow item when space is limited', async () => {
  Object.defineProperty(HTMLDivElement.prototype, 'clientWidth', { configurable: true, value: 0 });
  Object.defineProperty(HTMLButtonElement.prototype, 'offsetWidth', { configurable: true, value: 100 });
  Object.defineProperty(HTMLAnchorElement.prototype, 'offsetWidth', { configurable: true, value: 100 });

  render(
    <MemoryRouter>
      <OverflowNav items={[{ label: 'Questions', href: '/admin/questions' }]} />
    </MemoryRouter>,
  );

  const more = await screen.findByLabelText('more');
  more.click();
  const link = await screen.findByRole('menuitem', { name: 'Questions' });
  expect(link).toHaveAttribute('href', '/admin/questions');
});
