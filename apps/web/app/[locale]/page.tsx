// Imports the dependency used by this module.
import { getTranslations, setRequestLocale } from 'next-intl/server';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';

// Exports this declaration as the module default.
export default async function LandingPage({ params }: { params: Promise<{ locale: string }> }) {
  // Executes this line as the next step in the surrounding logic.
  const { locale } = await params;
  // Calls setRequestLocale with the supplied values.
  setRequestLocale(locale);
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Landing');

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="landing-page">
      {/* Renders the section interface element or component. */}
      <section className="hero-section" aria-labelledby="hero-title">
        {/* Renders the div interface element or component. */}
        <div className="hero-copy">
          {/* Renders the p interface element or component. */}
          <p className="mode-label">{t('eyebrow')}</p>
          {/* Renders the h1 interface element or component. */}
          <h1 id="hero-title">{t('title')}</h1>
          {/* Renders the p interface element or component. */}
          <p>{t('intro')}</p>
          {/* Renders the div interface element or component. */}
          <div className="button-row">
            {/* Renders the Link interface element or component. */}
            <Link className="button primary" href="/play">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('playNow')}
              {/* Closes the Link interface element. */}
            </Link>
            {/* Renders the Link interface element or component. */}
            <Link className="button secondary" href="/daily">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('todaysPuzzle')}
              {/* Closes the Link interface element. */}
            </Link>
            {/* Closes the div interface element. */}
          </div>
          {/* Closes the div interface element. */}
        </div>
        {/* Renders the div interface element or component. */}
        <div className="hero-board" aria-hidden="true">
          {/* Renders the div interface element or component. */}
          <div className="hero-code">
            {/* Renders the i interface element or component. */}
            <i className="peg peg-R">●</i>
            {/* Renders the i interface element or component. */}
            <i className="peg peg-B">◆</i>
            {/* Renders the i interface element or component. */}
            <i className="peg peg-G">▲</i>
            {/* Renders the i interface element or component. */}
            <i className="peg peg-Y">■</i>
            {/* Closes the div interface element. */}
          </div>
          {/* Renders the div interface element or component. */}
          <div className="hero-deduction">
            {/* Renders the span interface element or component. */}
            <span>● ○ ○</span>
            {/* Renders the span interface element or component. */}
            <span>● ● ○</span>
            {/* Renders the span interface element or component. */}
            <span>● ● ● ●</span>
            {/* Closes the div interface element. */}
          </div>
          {/* Closes the div interface element. */}
        </div>
        {/* Closes the section interface element. */}
      </section>

      {/* Renders the section interface element or component. */}
      <section className="explainer-section" aria-labelledby="how-title">
        {/* Renders the h2 interface element or component. */}
        <h2 id="how-title">{t('howItWorks')}</h2>
        {/* Renders the ol interface element or component. */}
        <ol className="step-list">
          {/* Renders the li interface element or component. */}
          <li>
            {/* Renders the span interface element or component. */}
            <span>1</span>
            {/* Renders the div interface element or component. */}
            <div>
              {/* Renders the h3 interface element or component. */}
              <h3>{t('stepOneTitle')}</h3>
              {/* Renders the p interface element or component. */}
              <p>{t('stepOneBody')}</p>
              {/* Closes the div interface element. */}
            </div>
            {/* Closes the li interface element. */}
          </li>
          {/* Renders the li interface element or component. */}
          <li>
            {/* Renders the span interface element or component. */}
            <span>2</span>
            {/* Renders the div interface element or component. */}
            <div>
              {/* Renders the h3 interface element or component. */}
              <h3>{t('stepTwoTitle')}</h3>
              {/* Renders the p interface element or component. */}
              <p>{t('stepTwoBody')}</p>
              {/* Closes the div interface element. */}
            </div>
            {/* Closes the li interface element. */}
          </li>
          {/* Renders the li interface element or component. */}
          <li>
            {/* Renders the span interface element or component. */}
            <span>3</span>
            {/* Renders the div interface element or component. */}
            <div>
              {/* Renders the h3 interface element or component. */}
              <h3>{t('stepThreeTitle')}</h3>
              {/* Renders the p interface element or component. */}
              <p>{t('stepThreeBody')}</p>
              {/* Closes the div interface element. */}
            </div>
            {/* Closes the li interface element. */}
          </li>
          {/* Closes the ol interface element. */}
        </ol>
        {/* Closes the section interface element. */}
      </section>

      {/* Renders the section interface element or component. */}
      <section className="mode-section" aria-labelledby="modes-title">
        {/* Renders the h2 interface element or component. */}
        <h2 id="modes-title">{t('modesTitle')}</h2>
        {/* Renders the div interface element or component. */}
        <div className="mode-list">
          {/* Renders the article interface element or component. */}
          <article>
            {/* Renders the h3 interface element or component. */}
            <h3>{t('soloTitle')}</h3>
            {/* Renders the p interface element or component. */}
            <p>{t('soloBody')}</p>
            {/* Renders the Link interface element or component. */}
            <Link href="/play">{t('playNow')} →</Link>
            {/* Closes the article interface element. */}
          </article>
          {/* Renders the article interface element or component. */}
          <article>
            {/* Renders the h3 interface element or component. */}
            <h3>{t('dailyTitle')}</h3>
            {/* Renders the p interface element or component. */}
            <p>{t('dailyBody')}</p>
            {/* Renders the Link interface element or component. */}
            <Link href="/daily">{t('todaysPuzzle')} →</Link>
            {/* Closes the article interface element. */}
          </article>
          {/* Renders the article interface element or component. */}
          <article>
            {/* Renders the h3 interface element or component. */}
            <h3>{t('friendsTitle')}</h3>
            {/* Renders the p interface element or component. */}
            <p>{t('friendsBody')}</p>
            {/* Renders the Link interface element or component. */}
            <Link href="/challenges/new">{t('friendsTitle')} →</Link>
            {/* Closes the article interface element. */}
          </article>
          {/* Closes the div interface element. */}
        </div>
        {/* Closes the section interface element. */}
      </section>

      {/* Renders the section interface element or component. */}
      <section className="trust-section">
        {/* Renders the article interface element or component. */}
        <article>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('fairTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('fairBody')}</p>
          {/* Closes the article interface element. */}
        </article>
        {/* Renders the article interface element or component. */}
        <article>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('accessibleTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('accessibleBody')}</p>
          {/* Closes the article interface element. */}
        </article>
        {/* Closes the section interface element. */}
      </section>

      {/* Renders the section interface element or component. */}
      <section className="closing-section">
        {/* Renders the h2 interface element or component. */}
        <h2>{t('ctaTitle')}</h2>
        {/* Renders the p interface element or component. */}
        <p>{t('ctaBody')}</p>
        {/* Renders the Link interface element or component. */}
        <Link className="button primary" href="/play">
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('playNow')}
          {/* Closes the Link interface element. */}
        </Link>
        {/* Closes the section interface element. */}
      </section>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
