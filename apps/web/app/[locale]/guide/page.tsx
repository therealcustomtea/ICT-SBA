import { getTranslations } from 'next-intl/server';
import { FeaturePage } from '@/components/feature-page';
import { Link } from '@/i18n/navigation';

export default async function GuidePage() {
  const t = await getTranslations('Guide');
  return (
    <FeaturePage
      title={t('title')}
      intro={t('intro')}
      actions={
        <Link className="button primary" href="/play">
          {t('start')}
        </Link>
      }
    >
      <div className="reading-layout">
        <section>
          <h2>{t('objectiveTitle')}</h2>
          <p>{t('objectiveBody')}</p>
        </section>
        <section>
          <h2>{t('feedbackTitle')}</h2>
          <div className="definition-list">
            <article>
              <span className="clue solid" aria-hidden="true">
                ●
              </span>
              <div>
                <h3>{t('exactTitle')}</h3>
                <p>{t('exactBody')}</p>
              </div>
            </article>
            <article>
              <span className="clue outline" aria-hidden="true">
                ○
              </span>
              <div>
                <h3>{t('colourTitle')}</h3>
                <p>{t('colourBody')}</p>
              </div>
            </article>
          </div>
          <p className="quiet-note">{t('feedbackNote')}</p>
        </section>
        <section>
          <h2>{t('keyboardTitle')}</h2>
          <p>{t('keyboardBody')}</p>
        </section>
        <section>
          <h2>{t('strategyTitle')}</h2>
          <p>{t('strategyBody')}</p>
        </section>
        <section>
          <h2>{t('duplicatesTitle')}</h2>
          <p>{t('duplicatesBody')}</p>
        </section>
        <section>
          <h2>{t('fairnessTitle')}</h2>
          <p>{t('fairnessBody')}</p>
        </section>
      </div>
    </FeaturePage>
  );
}
