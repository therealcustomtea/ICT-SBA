// Imports the dependency used by this module.
import { getTranslations } from 'next-intl/server';
// Imports the dependency used by this module.
import { Link } from '@/i18n/navigation';

// Exports this declaration as the module default.
export default async function NotFoundPage() {
  // Computes and stores t for subsequent operations.
  const t = await getTranslations('Errors');
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="page-shell">
      {/* Renders the section interface element or component. */}
      <section className="state-panel">
        {/* Renders the h1 interface element or component. */}
        <h1>{t('notFoundTitle')}</h1>
        {/* Renders the p interface element or component. */}
        <p>{t('notFoundBody')}</p>
        {/* Renders the div interface element or component. */}
        <div className="button-row">
          {/* Renders the Link interface element or component. */}
          <Link className="button primary" href="/">
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('home')}
            {/* Closes the Link interface element. */}
          </Link>
          {/* Renders the Link interface element or component. */}
          <Link className="button secondary" href="/play">
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('newGame')}
            {/* Closes the Link interface element. */}
          </Link>
          {/* Closes the div interface element. */}
        </div>
        {/* Closes the section interface element. */}
      </section>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
