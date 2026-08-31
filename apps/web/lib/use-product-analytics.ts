// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useLocale } from 'next-intl';
// Imports the dependency used by this module.
import { useCallback } from 'react';
// Imports the dependency used by this module.
import { useSession } from '@/components/session-provider';
// Imports the dependency used by this module.
import { type AnalyticsEventMap, deliverProductEvent } from './analytics-delivery';

// Exports this declaration for use by other modules.
export function useProductAnalytics() {
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Executes this line as the next step in the surrounding logic.
  const { getAccessToken } = useSession();
  // Returns this result to the caller and ends the current function.
  return useCallback(
    // Renders the K interface element or component.
    <K extends keyof AnalyticsEventMap>(eventName: K, fields: AnalyticsEventMap[K]) => {
      // Executes this line as the next step in the surrounding logic.
      void getAccessToken().then(
        // Continues the surrounding operation with this required value or expression.
        (token) =>
          // Calls deliverProductEvent with the supplied values.
          deliverProductEvent(token, locale === 'zh-Hant' ? 'zh-Hant' : 'en', eventName, fields),
        // Closes the expression, call, or declaration started above.
      );
      // Closes the expression, call, or declaration started above.
    },
    // Supplies this item to the surrounding call or collection.
    [getAccessToken, locale],
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
