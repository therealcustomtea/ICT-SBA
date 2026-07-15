import { defineRouting } from 'next-intl/routing';

export const routing = defineRouting({
  locales: ['en', 'zh-Hant'],
  defaultLocale: 'en',
  localePrefix: 'always',
});
