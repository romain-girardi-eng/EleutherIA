import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'src/archive/**']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs['recommended-latest'],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Relax 'any' type restriction - warn instead of error
      '@typescript-eslint/no-explicit-any': 'warn',
      // Allow unused vars that start with underscore or 'e' for error handlers
      '@typescript-eslint/no-unused-vars': ['error', {
        'argsIgnorePattern': '^(_|e$)',
        'varsIgnorePattern': '^_',
        'caughtErrorsIgnorePattern': '^_',
      }],
      // Allow exporting constants with components (common pattern)
      'react-refresh/only-export-components': 'warn',
      // Allow lexical declarations in case blocks
      'no-case-declarations': 'off',
      // Relax const preference for let (allow developer choice)
      'prefer-const': 'warn',
      // Allow @ts-ignore comments (sometimes necessary)
      '@typescript-eslint/ban-ts-comment': 'warn',
      // Allow irregular whitespace in strings (for special characters)
      'no-irregular-whitespace': ['error', { 'skipStrings': true, 'skipComments': true }],
    },
  },
  // Relaxed rules for test files
  {
    files: ['**/*.test.{ts,tsx}', '**/tests/**/*.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  // Relaxed rules for type declaration files
  {
    files: ['**/*.d.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  // Relaxed rules for context files (fast refresh doesn't apply)
  {
    files: ['**/context/**/*.{ts,tsx}'],
    rules: {
      'react-refresh/only-export-components': 'off',
    },
  },
])
