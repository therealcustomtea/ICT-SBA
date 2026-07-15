import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { AchievementsPanel } from '../_components/data-panels';

export const metadata = { robots: { index: false, follow: false } };

export default async function AchievementsPage() {
  const t = await getTranslations('Achievements');
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <AchievementsPanel />
    </FeaturePage>
  );
}
