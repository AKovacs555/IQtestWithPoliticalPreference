import { useEffect } from 'react';
import i18n from '../i18n';

export default function usePersistedLang() {
  useEffect(() => {
    const lang = localStorage.getItem('i18nLang');
    if (lang && lang !== i18n.language && !window.location.pathname.startsWith('/admin')) {
      i18n.changeLanguage(lang);
    }
    document.documentElement.lang = i18n.language;
    const handle = (lng) => {
      document.documentElement.lang = lng;
    };
    i18n.on('languageChanged', handle);
    return () => i18n.off('languageChanged', handle);
  }, []);
}
