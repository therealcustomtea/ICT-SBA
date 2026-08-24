// Imports the dependency used by this module.
import { defineConfig, globalIgnores } from 'eslint/config';
// Imports the dependency used by this module.
import nextVitals from 'eslint-config-next/core-web-vitals';
// Imports the dependency used by this module.
import nextTypescript from 'eslint-config-next/typescript';

// Exports this declaration as the module default.
export default defineConfig([
  // Supplies this item to the surrounding call or collection.
  ...nextVitals,
  // Supplies this item to the surrounding call or collection.
  ...nextTypescript,
  // Calls globalIgnores with the supplied values.
  globalIgnores(['.next/**', 'coverage/**', 'playwright-report/**', 'next-env.d.ts']),
// Closes the expression, call, or declaration started above.
]);
