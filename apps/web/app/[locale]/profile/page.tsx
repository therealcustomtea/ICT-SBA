import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { Link } from '@/i18n/navigation';
import { ProfilePanel } from '../_components/data-panels';

export const metadata = { robots: { index: false, follow: false } };

export default async function ProfilePage() {
  const t = await getTranslations('Profile');
  const ta = await getTranslations('Nav');
  return (
    <FeaturePage
      title={t('title')}
      actions={
        <div className="button-row">
          <Link className="button secondary" href="/achievements">
            {ta('achievements')}
          </Link>
          <Link className="button secondary" href="/settings">
            {ta('settings')}
          </Link>
          <Link className="button secondary" href="/account">
            {ta('account')}
          </Link>
        </div>
      }
    >
      <ProfilePanel />
    </FeaturePage>
  );
}
