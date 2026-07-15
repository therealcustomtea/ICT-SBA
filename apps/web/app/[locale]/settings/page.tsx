import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { SettingsForm } from '../_components/account-panels';
export const metadata = { robots: { index: false, follow: false } };
export default async function SettingsPage() {
  const t = await getTranslations('Settings');
  return (
    <FeaturePage title={t('title')}>
      <SettingsForm />
    </FeaturePage>
  );
}
