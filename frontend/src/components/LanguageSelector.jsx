import React from 'react';
import { useTranslation } from 'react-i18next';

export default function LanguageSelector() {
  const { i18n: i18nInstance } = useTranslation();
  const languages = [
    { code: 'en', label: 'English' },
    { code: 'ja', label: '日本語' },
    { code: 'tr', label: 'Türkçe' },
    { code: 'ru', label: 'Русский' },
    { code: 'zh', label: '中文' },
    { code: 'ko', label: '한국어' },
    { code: 'es', label: 'Español' },
    { code: 'fr', label: 'Français' },
    { code: 'it', label: 'Italiano' },
    { code: 'de', label: 'Deutsch' },
    { code: 'ar', label: 'العربية' }
  ];
  const handleChange = (e) => {
    const lang = e.target.value;
    i18nInstance.changeLanguage(lang);
    localStorage.setItem('i18nLang', lang);
  };
  return (
    <select
      value={i18nInstance.language}
      onChange={handleChange}
      className="border rounded-md px-2 py-2 text-sm"
      aria-label="Select language"
    >
      {languages.map(l => (
        <option key={l.code} value={l.code} lang={l.code}>
          {l.label}
        </option>
      ))}
    </select>
  );
}
