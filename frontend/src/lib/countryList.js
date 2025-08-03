import countries from 'i18n-iso-countries';
import ar from 'i18n-iso-countries/langs/ar.json';
import de from 'i18n-iso-countries/langs/de.json';
import en from 'i18n-iso-countries/langs/en.json';
import es from 'i18n-iso-countries/langs/es.json';
import fr from 'i18n-iso-countries/langs/fr.json';
import it from 'i18n-iso-countries/langs/it.json';
import ja from 'i18n-iso-countries/langs/ja.json';
import ko from 'i18n-iso-countries/langs/ko.json';
import ru from 'i18n-iso-countries/langs/ru.json';
import tr from 'i18n-iso-countries/langs/tr.json';
import zh from 'i18n-iso-countries/langs/zh.json';

countries.registerLocale(ar);
countries.registerLocale(de);
countries.registerLocale(en);
countries.registerLocale(es);
countries.registerLocale(fr);
countries.registerLocale(it);
countries.registerLocale(ja);
countries.registerLocale(ko);
countries.registerLocale(ru);
countries.registerLocale(tr);
countries.registerLocale(zh);

export default function countryList(lang = 'en') {
  const names = countries.getNames(lang, { select: 'official' }) || {};
  return Object.entries(names)
    .map(([code, name]) => ({ code, name }))
    .sort((a, b) => a.name.localeCompare(b.name));
}
