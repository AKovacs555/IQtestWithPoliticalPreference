import React from 'react';
import { useTranslation } from 'react-i18next';

export default function LanguageSelector() {
  const { i18n: i18nInstance } = useTranslation();
  const languages = [
    { code: 'en', label: 'English' },
    { code: 'ja', label: '日本語' },
    { code: 'tr', label: 'Türkçe' },
    { code: 'ru', label: 'Русский' },
    { code: 'zh', label: '中文' }
  ];
  const handleChange = (e) => {
    const lang = e.target.value;
    i18nInstance.changeLanguage(lang);
    localStorage.setItem('i18nLang', lang);
  };
  return (
    <select value={i18nInstance.language} onChange={handleChange} className="select select-bordered select-sm">
      {languages.map(l => (
        <option key={l.code} value={l.code}>{l.label}</option>
      ))}
    </select>
  );
}
