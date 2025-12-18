const reactHooks = require("eslint-plugin-react-hooks");

module.exports = [
  {
    files: ["src/**/*.{js,jsx}"],
    ignores: ["src/__tests__/**"],
    plugins: {
      "react-hooks": reactHooks,
    },
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      // Optional rule (supported in newer plugin versions). Keep as warn to avoid build blocks.
      "react-hooks/set-state-in-effect": "warn",
    },
  },
];
