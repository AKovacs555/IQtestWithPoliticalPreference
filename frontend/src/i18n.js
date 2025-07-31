import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from '../translations/en.json';
import ja from '../translations/ja.json';
import tr from '../translations/tr.json';
import ru from '../translations/ru.json';
import zh from '../translations/zh.json';

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ja: { translation: ja },
    tr: { translation: tr },
    ru: { translation: ru },
    zh: { translation: zh },
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
