// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { createBrowserClient } from '@supabase/ssr';

// Exports this declaration for use by other modules.
export const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? '';
// Exports this declaration for use by other modules.
export const supabasePublishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? '';

// Exports this declaration for use by other modules.
export const isSupabaseConfigured = Boolean(supabaseUrl && supabasePublishableKey);

// Exports this declaration for use by other modules.
export function createSupabaseBrowserClient() {
  // Checks this condition before running the nested branch.
  if (!isSupabaseConfigured) return null;
  // Returns this result to the caller and ends the current function.
  return createBrowserClient(supabaseUrl, supabasePublishableKey);
  // Closes the expression, call, or declaration started above.
}
