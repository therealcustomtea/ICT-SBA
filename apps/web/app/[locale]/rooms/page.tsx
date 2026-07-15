import { getTranslations } from 'next-intl/server';
import { Suspense } from 'react';
import { FeaturePage } from '@/components/feature-page';
import { AsyncState } from '@/components/feature-page';
import { RoomEntry } from '../_components/room-panels';

export const metadata = { robots: { index: false, follow: false } };

export default async function RoomsPage() {
  const t = await getTranslations('Rooms');
  const tc = await getTranslations('Common');
  return (
    <FeaturePage title={t('newTitle')} intro={t('newIntro')}>
      <Suspense
        fallback={
          <AsyncState
            state="loading"
            loadingLabel={tc('loading')}
            errorLabel={tc('loadError')}
            emptyLabel={tc('empty')}
          />
        }
      >
        <RoomEntry />
      </Suspense>
    </FeaturePage>
  );
}
