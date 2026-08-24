// Imports the dependency used by this module.
import { defineConfig, devices } from '@playwright/test';

// Computes and stores baseURL for subsequent operations.
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:3000';
// Computes and stores serverPort for subsequent operations.
const serverPort = new URL(baseURL).port || (baseURL.startsWith('https:') ? '443' : '80');

// Exports this declaration as the module default.
export default defineConfig({
  // Defines the testDir field in the surrounding object or type.
  testDir: './e2e',
  // Defines the timeout field in the surrounding object or type.
  timeout: 30_000,
  // Defines the forbidOnly field in the surrounding object or type.
  forbidOnly: Boolean(process.env.CI),
  // Defines the workers field in the surrounding object or type.
  workers: process.env.CI ? 1 : undefined,
  // Defines the retries field in the surrounding object or type.
  retries: process.env.CI ? 2 : 0,
  // Defines the reporter field in the surrounding object or type.
  reporter: [['html', { open: 'never' }], ['list']],
  // Defines the use field in the surrounding object or type.
  use: {
    // Supplies this item to the surrounding call or collection.
    baseURL,
    // Defines the screenshot field in the surrounding object or type.
    screenshot: 'only-on-failure',
    // Defines the trace field in the surrounding object or type.
    trace: 'retain-on-failure',
    // Closes the expression, call, or declaration started above.
  },
  // Defines the webServer field in the surrounding object or type.
  webServer: process.env.PLAYWRIGHT_SKIP_WEBSERVER
    ? // Executes this line as the next step in the surrounding logic.
      undefined
    : // Begins the nested block or object completed below.
      {
        // Defines the command field in the surrounding object or type.
        command: `pnpm exec next dev --hostname 127.0.0.1 --port ${serverPort}`,
        // Defines the url field in the surrounding object or type.
        url: `${baseURL}/en`,
        // Defines the reuseExistingServer field in the surrounding object or type.
        reuseExistingServer: !process.env.CI,
        // Closes the expression, call, or declaration started above.
      },
  // Defines the projects field in the surrounding object or type.
  projects: [
    // Supplies this item to the surrounding call or collection.
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    // Supplies this item to the surrounding call or collection.
    { name: 'mobile', use: { ...devices['iPhone 14'] } },
    // Closes the expression, call, or declaration started above.
  ],
  // Closes the expression, call, or declaration started above.
});
