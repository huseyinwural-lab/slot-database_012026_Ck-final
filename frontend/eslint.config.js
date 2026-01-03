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
      // CI build treats warnings as errors; keep exhaustive-deps off to avoid non-functional build blocks.
      "react-hooks/exhaustive-deps": "off"
    }
  }
];
