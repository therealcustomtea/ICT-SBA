// Imports the dependency used by this module.
import eslint from '@eslint/js';
// Imports the dependency used by this module.
import tseslint from 'typescript-eslint';

// Exports this declaration as the module default.
export default tseslint.config(eslint.configs.recommended, ...tseslint.configs.strict, {
  // Defines the ignores field in the surrounding object or type.
  ignores: ['src/schema.ts'],
// Closes the expression, call, or declaration started above.
});
