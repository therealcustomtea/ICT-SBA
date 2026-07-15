import { getTranslations, setRequestLocale } from 'next-intl/server';
import { Link } from '@/i18n/navigation';

export default async function LandingPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('Landing');

  return (
    <div className="landing-page">
      <section className="hero-section" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="mode-label">{t('eyebrow')}</p>
          <h1 id="hero-title">{t('title')}</h1>
          <p>{t('intro')}</p>
          <div className="button-row">
            <Link className="button primary" href="/play">
              {t('playNow')}
            </Link>
            <Link className="button secondary" href="/daily">
              {t('todaysPuzzle')}
            </Link>
          </div>
        </div>
        <div className="hero-board" aria-hidden="true">
          <div className="hero-code">
            <i className="peg peg-R">●</i>
            <i className="peg peg-B">◆</i>
            <i className="peg peg-G">▲</i>
            <i className="peg peg-Y">■</i>
          </div>
          <div className="hero-deduction">
            <span>● ○ ○</span>
            <span>● ● ○</span>
            <span>● ● ● ●</span>
          </div>
        </div>
      </section>

      <section className="explainer-section" aria-labelledby="how-title">
        <h2 id="how-title">{t('howItWorks')}</h2>
        <ol className="step-list">
          <li>
            <span>1</span>
            <div>
              <h3>{t('stepOneTitle')}</h3>
              <p>{t('stepOneBody')}</p>
            </div>
          </li>
          <li>
            <span>2</span>
            <div>
              <h3>{t('stepTwoTitle')}</h3>
              <p>{t('stepTwoBody')}</p>
            </div>
          </li>
          <li>
            <span>3</span>
            <div>
              <h3>{t('stepThreeTitle')}</h3>
              <p>{t('stepThreeBody')}</p>
            </div>
          </li>
        </ol>
      </section>

      <section className="mode-section" aria-labelledby="modes-title">
        <h2 id="modes-title">{t('modesTitle')}</h2>
        <div className="mode-list">
          <article>
            <h3>{t('soloTitle')}</h3>
            <p>{t('soloBody')}</p>
            <Link href="/play">{t('playNow')} →</Link>
          </article>
          <article>
            <h3>{t('dailyTitle')}</h3>
            <p>{t('dailyBody')}</p>
            <Link href="/daily">{t('todaysPuzzle')} →</Link>
          </article>
          <article>
            <h3>{t('friendsTitle')}</h3>
            <p>{t('friendsBody')}</p>
            <Link href="/challenges/new">{t('friendsTitle')} →</Link>
          </article>
        </div>
      </section>

      <section className="trust-section">
        <article>
          <h2>{t('fairTitle')}</h2>
          <p>{t('fairBody')}</p>
        </article>
        <article>
          <h2>{t('accessibleTitle')}</h2>
          <p>{t('accessibleBody')}</p>
        </article>
      </section>

      <section className="closing-section">
        <h2>{t('ctaTitle')}</h2>
        <p>{t('ctaBody')}</p>
        <Link className="button primary" href="/play">
          {t('playNow')}
        </Link>
      </section>
    </div>
  );
}
