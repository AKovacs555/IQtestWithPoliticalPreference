import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from '../translations/en.json';
import ja from '../translations/ja.json';
import tr from '../translations/tr.json';
import ru from '../translations/ru.json';
import zh from '../translations/zh.json';
import ko from '../translations/ko.json';
import es from '../translations/es.json';
import fr from '../translations/fr.json';
import it from '../translations/it.json';
import de from '../translations/de.json';
import ar from '../translations/ar.json';

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ja: { translation: ja },
    tr: { translation: tr },
    ru: { translation: ru },
    zh: { translation: zh },
    ko: { translation: ko },
    es: { translation: es },
    fr: { translation: fr },
    it: { translation: it },
    de: { translation: de },
    ar: { translation: ar },
  },
  lng: localStorage.getItem('i18nLang') || 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

i18n.on('languageChanged', (lng) => {
  localStorage.setItem('i18nLang', lng);
});

export default i18n;
