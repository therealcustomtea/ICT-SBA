// Imports the dependency used by this module.
import { getRequestConfig } from 'next-intl/server';
// Imports the dependency used by this module.
import { hasLocale } from 'next-intl';
// Imports the dependency used by this module.
import { routing } from './routing';

// Exports this declaration as the module default.
export default getRequestConfig(async ({ requestLocale }) => {
  // Computes and stores requested for subsequent operations.
  const requested = await requestLocale;
  // Computes and stores locale for subsequent operations.
  const locale = hasLocale(routing.locales, requested) ? requested : routing.defaultLocale;
  // Returns this result to the caller and ends the current function.
  return {
    // Supplies this item to the surrounding call or collection.
    locale,
    // Defines the messages field in the surrounding object or type.
    messages: (await import(`../messages/${locale}.json`)).default,
    // Closes the expression, call, or declaration started above.
  };
  // Closes the expression, call, or declaration started above.
});
