import data from 'country-json/src/country-by-abbreviation.json';

// Map the external JSON into code/name pairs
export default data.map((c) => ({ code: c.abbreviation, name: c.country }));
