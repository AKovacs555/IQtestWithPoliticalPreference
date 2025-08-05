import countries from 'i18n-iso-countries';
import en from 'i18n-iso-countries/langs/en.json';
import fr from 'i18n-iso-countries/langs/fr.json';
import de from 'i18n-iso-countries/langs/de.json';
import ru from 'i18n-iso-countries/langs/ru.json';
import zh from 'i18n-iso-countries/langs/zh.json';
import tr from 'i18n-iso-countries/langs/tr.json';
import it from 'i18n-iso-countries/langs/it.json';
import ar from 'i18n-iso-countries/langs/ar.json';
import es from 'i18n-iso-countries/langs/es.json';
import ko from 'i18n-iso-countries/langs/ko.json';
import ja from 'i18n-iso-countries/langs/ja.json';

// Register all locales used by the application.
// This allows country names to be retrieved in the selected language.
[
  en,
  fr,
  de,
  ru,
  zh,
  tr,
  it,
  ar,
  es,
  ko,
  ja,
].forEach(locale => countries.registerLocale(locale));

/**
 * Retrieve the list of countries in the given language.
 * Falls back to English if the language is not supported.
 *
 * @param {string} lang - i18next language code (e.g. "en", "fr").
 * @returns {{code: string, name: string}[]} Array of countries.
 */
function getCountryList(lang = 'en') {
  const base = lang.split('-')[0];
  let names = countries.getNames(base, { select: 'official' });
  if (!Object.keys(names).length) {
    names = countries.getNames('en', { select: 'official' });
  }
  return Object.entries(names).map(([code, name]) => ({ code, name }));
}

export default getCountryList;

