// ESLint 9 flat config for the API worker.
// Introduced when CI stopped masking lint failures (`pnpm lint || true`) —
// previously there was no config at all and eslint exited with a hard error.
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['.wrangler/**', 'coverage/**', 'node_modules/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    rules: {
      // The codebase intentionally prefixes unused-but-required params with _
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  }
);
