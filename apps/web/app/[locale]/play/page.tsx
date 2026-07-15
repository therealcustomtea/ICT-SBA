import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { SetupForm } from '../_components/setup-form';

export default async function PlaySetupPage() {
  const t = await getTranslations('Play');
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <SetupForm />
    </FeaturePage>
  );
}
