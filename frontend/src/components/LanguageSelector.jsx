import React from 'react';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES } from '../i18n/languages';

export default function LanguageSelector({ className = '' }) {
  const { i18n: i18nInstance } = useTranslation();
  const languages = Object.entries(SUPPORTED_LANGUAGES);
  const handleChange = (e) => {
    const lang = e.target.value;
    i18nInstance.changeLanguage(lang);
    localStorage.setItem('i18nLang', lang);
  };
  return (
    <select
      value={i18nInstance.language}
      onChange={handleChange}
      className={`h-8 px-3 rounded-full border border-[rgba(148,163,184,.25)] bg-transparent text-sm text-[var(--text)] hover:bg-[rgba(6,182,212,.08)] ${className}`}
      aria-label="Select language"
    >
      {languages.map(([code, label]) => (
        <option key={code} value={code} lang={code} className="text-gray-900 dark:text-gray-100">
          {label}
        </option>
      ))}
    </select>
  );
}
