import { useEffect } from 'react';
import i18n from '../i18n';

export default function usePersistedLang() {
  useEffect(() => {
    const lang = localStorage.getItem('i18nLang');
    if (lang && lang !== i18n.language && !window.location.pathname.startsWith('/admin')) {
      i18n.changeLanguage(lang);
    }
  }, []);
}
