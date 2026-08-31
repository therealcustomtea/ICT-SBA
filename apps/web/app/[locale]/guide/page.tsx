// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { FeaturePage } from '@/components/feature-page';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';

// Exports this declaration as the module default.
export default async function GuidePage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Guide');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the FeaturePage interface element or component.
    <FeaturePage
      /* Provides the title value to the surrounding call or element. */
      title={t('title')}
      /* Provides the intro value to the surrounding call or element. */
      intro={t('intro')}
      /* Provides the actions value to the surrounding call or element. */
      actions={
        // Renders the Link interface element or component.
        <Link className="button primary" href="/play">
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('start')}
          {/* Closes the Link interface element. */}
        </Link>
        // Closes the expression, call, or declaration started above.
      }
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Renders the div interface element or component. */}
      <div className="reading-layout">
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('objectiveTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('objectiveBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('feedbackTitle')}</h2>
          {/* Renders the div interface element or component. */}
          <div className="definition-list">
            {/* Renders the article interface element or component. */}
            <article>
              {/* Renders the span interface element or component. */}
              <span className="clue solid" aria-hidden="true">
                ●{/* Closes the span interface element. */}
              </span>
              {/* Renders the div interface element or component. */}
              <div>
                {/* Renders the h3 interface element or component. */}
                <h3>{t('exactTitle')}</h3>
                {/* Renders the p interface element or component. */}
                <p>{t('exactBody')}</p>
                {/* Closes the div interface element. */}
              </div>
              {/* Closes the article interface element. */}
            </article>
            {/* Renders the article interface element or component. */}
            <article>
              {/* Renders the span interface element or component. */}
              <span className="clue outline" aria-hidden="true">
                ○{/* Closes the span interface element. */}
              </span>
              {/* Renders the div interface element or component. */}
              <div>
                {/* Renders the h3 interface element or component. */}
                <h3>{t('colourTitle')}</h3>
                {/* Renders the p interface element or component. */}
                <p>{t('colourBody')}</p>
                {/* Closes the div interface element. */}
              </div>
              {/* Closes the article interface element. */}
            </article>
            {/* Closes the div interface element. */}
          </div>
          {/* Renders the p interface element or component. */}
          <p className="quiet-note">{t('feedbackNote')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('keyboardTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('keyboardBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('strategyTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('strategyBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('duplicatesTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('duplicatesBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Renders the section interface element or component. */}
        <section>
          {/* Renders the h2 interface element or component. */}
          <h2>{t('fairnessTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('fairnessBody')}</p>
          {/* Closes the section interface element. */}
        </section>
        {/* Closes the div interface element. */}
      </div>
      {/* Closes the FeaturePage interface element. */}
    </FeaturePage>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
