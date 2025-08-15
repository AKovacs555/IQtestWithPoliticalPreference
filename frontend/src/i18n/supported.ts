import { SUPPORTED_LANGUAGES } from './languages';

export const SUPPORTED_LANGS = Object.entries(SUPPORTED_LANGUAGES).map(([code, label]) => ({
  code,
  label,
}));
