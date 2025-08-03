import countries from 'i18n-iso-countries';
import en from 'i18n-iso-countries/langs/en.json';
import ja from 'i18n-iso-countries/langs/ja.json';

// Register the supported locales so we can retrieve localized country names
countries.registerLocale(en);
countries.registerLocale(ja);

/**
 * Return an array of countries for the given language.
 * Each element has the ISO code (alpha-2) and localized name.
 */
export default function getCountryList(lang = 'en') {
  const names = countries.getNames(lang, { select: 'official' });
  return Object.entries(names).map(([code, name]) => ({ code, name }));
}

