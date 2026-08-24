// Imports the dependency used by this module.
import { createNavigation } from 'next-intl/navigation';
// Imports the dependency used by this module.
import { routing } from './routing';

// Exports this declaration for use by other modules.
export const { Link, redirect, usePathname, useRouter, getPathname } = createNavigation(routing);
