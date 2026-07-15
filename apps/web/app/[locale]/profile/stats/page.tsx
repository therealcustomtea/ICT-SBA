import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { ProfilePanel } from '../../_components/data-panels';

export const metadata = { robots: { index: false, follow: false } };

export default async function StatsPage() {
  const t = await getTranslations('Profile');
  return (
    <FeaturePage title={t('stats')}>
      <ProfilePanel statsOnly />
    </FeaturePage>
  );
}
