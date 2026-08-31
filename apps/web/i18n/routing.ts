// Imports the dependency used by this module.
import { defineRouting } from 'next-intl/routing';

// Exports this declaration for use by other modules.
export const routing = defineRouting({
  // Defines the locales field in the surrounding object or type.
  locales: ['en', 'zh-Hant'],
  // Defines the defaultLocale field in the surrounding object or type.
  defaultLocale: 'en',
  // Defines the localePrefix field in the surrounding object or type.
  localePrefix: 'always',
  // Closes the expression, call, or declaration started above.
});
