// Imports the dependency used by this module.
import { defineConfig } from 'vitest/config';
// Imports the dependency used by this module.
import path from 'node:path';

// Exports this declaration as the module default.
export default defineConfig({
  // Defines the resolve field in the surrounding object or type.
  resolve: { alias: { '@': path.resolve(__dirname, '.') } },
  // Defines the test field in the surrounding object or type.
  test: {
    // Defines the include field in the surrounding object or type.
    include: ['**/*.test.{ts,tsx}'],
    // Defines the exclude field in the surrounding object or type.
    exclude: ['e2e/**', 'node_modules/**', '.next/**'],
    // Defines the environment field in the surrounding object or type.
    environment: 'jsdom',
    // Defines the setupFiles field in the surrounding object or type.
    setupFiles: ['./test/setup.ts'],
    // Defines the coverage field in the surrounding object or type.
    coverage: {
      // Defines the provider field in the surrounding object or type.
      provider: 'istanbul',
      // Defines the reporter field in the surrounding object or type.
      reporter: ['text', 'json', 'html'],
      // Route orchestration has focused behavior tests; the numeric gate covers reusable components and libraries.
      // Defines the exclude field in the surrounding object or type.
      exclude: ['app/**/_components/**'],
      // Defines the thresholds field in the surrounding object or type.
      thresholds: { lines: 80, functions: 75, branches: 75, statements: 80 },
      // Closes the expression, call, or declaration started above.
    },
    // Closes the expression, call, or declaration started above.
  },
  // Closes the expression, call, or declaration started above.
});
