import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
  resolve: { alias: { '@': path.resolve(__dirname, '.') } },
  test: {
    include: ['**/*.test.{ts,tsx}'],
    exclude: ['e2e/**', 'node_modules/**', '.next/**'],
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    coverage: {
      provider: 'istanbul',
      reporter: ['text', 'json', 'html'],
      // Route orchestration has focused behavior tests; the numeric gate covers reusable components and libraries.
      exclude: ['app/**/_components/**'],
      thresholds: { lines: 80, functions: 75, branches: 75, statements: 80 },
    },
  },
});
