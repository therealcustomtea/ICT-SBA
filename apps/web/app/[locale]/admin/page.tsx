import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { AdminPanel } from '../_components/admin-panel';

export const metadata = { robots: { index: false, follow: false } };

export default async function AdminPage() {
  const t = await getTranslations('Admin');
  return (
    <FeaturePage title={t('title')} intro={t('intro')}>
      <AdminPanel />
    </FeaturePage>
  );
}
