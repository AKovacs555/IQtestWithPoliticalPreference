import React from 'react';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES } from '../i18n/languages';

export default function LanguageSelector() {
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
      className="border rounded-md px-3 py-2 text-base bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-100"
      aria-label="Select language"
    >
      {languages.map(([code, label]) => (
        <option key={code} value={code} lang={code}>
          {label}
        </option>
      ))}
    </select>
  );
}
