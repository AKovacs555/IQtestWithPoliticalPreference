import type { ReactNode } from 'react';

export interface NavItem {
  label: string;
  href?: string;
  onClick?: (e?: any) => void;
  element?: ReactNode;
}
