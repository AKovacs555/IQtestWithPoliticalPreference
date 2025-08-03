import countries from 'i18n-iso-countries';
import en from 'i18n-iso-countries/langs/en.json';

countries.registerLocale(en);

// Export a full ISO list with English names so translations can
// provide localized labels via i18next keys like `country_names.US`.
const countryList = Object.entries(
  countries.getNames('en', { select: 'official' })
).map(([code, name_en]) => ({ code, name_en }));

export default countryList;

