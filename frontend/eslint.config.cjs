module.exports = [
  {
    files: ['**/*.ts', '**/*.tsx'],
    ignores: ['node_modules'],
    languageOptions: {
      parser: require('@typescript-eslint/parser'),
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      '@typescript-eslint': require('@typescript-eslint/eslint-plugin'),
    },
    linterOptions: {
      reportUnusedDisableDirectives: false,
    },
    rules: {},
  },
];
