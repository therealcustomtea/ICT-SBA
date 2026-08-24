// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { Suspense } from 'react';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { AsyncState } from '@/components/feature-page';
// Imports the dependency used by this module.
import { RoomEntry } from '../_components/room-panels';

// Exports this declaration for use by other modules.
export const metadata = { robots: { index: false, follow: false } };

// Exports this declaration as the module default.
export default async function RoomsPage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Rooms');
  // Computes and stores tc for subsequent operations.
  const tc = await getTranslations('Common');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage title={t('newTitle')} intro={t('newIntro')}>
      {/* Renders the Suspense interface element or component. */}
      <Suspense
        /* Provides the fallback value to the surrounding call or element. */
        fallback={
          // Renders the AsyncState interface element or component.
          <AsyncState
            /* Provides the state value to the surrounding call or element. */
            state="loading"
            /* Provides the loadingLabel value to the surrounding call or element. */
            loadingLabel={tc('loading')}
            /* Provides the errorLabel value to the surrounding call or element. */
            errorLabel={tc('loadError')}
            /* Provides the emptyLabel value to the surrounding call or element. */
            emptyLabel={tc('empty')}
            /* Executes this line as the next step in the surrounding logic. */
          />
          // Closes the expression, call, or declaration started above.
        }
        /* Closes the expression, call, or declaration started above. */
      >
        {/* Renders the RoomEntry interface element or component. */}
        <RoomEntry />
        {/* Closes the Suspense interface element. */}
      </Suspense>
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
