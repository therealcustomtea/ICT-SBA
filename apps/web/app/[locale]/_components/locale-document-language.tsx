// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useEffect } from 'react';

// Exports this declaration for use by other modules.
export function LocaleDocumentLanguage({ locale }: { locale: string }) {
  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Executes this line as the next step in the surrounding logic.
    document.documentElement.lang = locale;
    // Executes this line as the next step in the surrounding logic.
  }, [locale]);
  // Returns this result to the caller and ends the current function.
  return null;
  // Closes the expression, call, or declaration started above.
}
