// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { Languages, Menu, Moon, Sun, UserRound, X } from 'lucide-react';
// Imports the dependency used by this module.
import { useLocale, useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useEffect, useState } from 'react';
// Imports the dependency used by this module.
import { Link, usePathname } from '@/i18n/navigation';
// Imports the dependency used by this module.
import { applyPreferences, loadPreferences, savePreferences } from '@/lib/preferences';
// Imports the dependency used by this module.
import { Logo } from './logo';
// Imports the dependency used by this module.
import { ServiceWorkerRegister } from './service-worker-register';
// Imports the dependency used by this module.
import { useSession } from './session-provider';

// Computes and stores navigation for subsequent operations.
const navigation = [
  // Supplies this item to the surrounding call or collection.
  ['play', '/play'],
  // Supplies this item to the surrounding call or collection.
  ['daily', '/daily'],
  // Supplies this item to the surrounding call or collection.
  ['challenges', '/challenges/new'],
  // Supplies this item to the surrounding call or collection.
  ['rooms', '/rooms'],
  // Executes this line as the next step in the surrounding logic.
] as const;

// Exports this declaration for use by other modules.
export function AppShell({ children }: { children: React.ReactNode }) {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('App');
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores pathname for subsequent operations.
  const pathname = usePathname();
  // Executes this line as the next step in the surrounding logic.
  const { status, isGuest } = useSession();
  // Executes this line as the next step in the surrounding logic.
  const [menuOpen, setMenuOpen] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [dark, setDark] = useState(false);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores colourScheme for subsequent operations.
    const colourScheme = matchMedia('(prefers-color-scheme: dark)');
    // Computes and stores syncPreferences for subsequent operations.
    const syncPreferences = () => {
      // Computes and stores preferences for subsequent operations.
      const preferences = loadPreferences();
      // Computes and stores nextDark for subsequent operations.
      const nextDark =
        // Executes this line as the next step in the surrounding logic.
        preferences.theme === 'dark' || (preferences.theme === 'system' && colourScheme.matches);
      // Calls setDark with the supplied values.
      setDark(nextDark);
      // Calls applyPreferences with the supplied values.
      applyPreferences(preferences);
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores handleColourScheme for subsequent operations.
    const handleColourScheme = () => {
      // Checks this condition before running the nested branch.
      if (loadPreferences().theme === 'system') syncPreferences();
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores frame for subsequent operations.
    const frame = requestAnimationFrame(syncPreferences);
    // Calls window.addEventListener with the supplied values.
    window.addEventListener('cipherboard:preferences-changed', syncPreferences);
    // Calls colourScheme.addEventListener with the supplied values.
    colourScheme.addEventListener('change', handleColourScheme);
    // Returns this result to the caller and ends the current function.
    return () => {
      // Calls cancelAnimationFrame with the supplied values.
      cancelAnimationFrame(frame);
      // Calls window.removeEventListener with the supplied values.
      window.removeEventListener('cipherboard:preferences-changed', syncPreferences);
      // Calls colourScheme.removeEventListener with the supplied values.
      colourScheme.removeEventListener('change', handleColourScheme);
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, []);

  // Computes and stores handleTheme for subsequent operations.
  const handleTheme = () => {
    // Computes and stores nextDark for subsequent operations.
    const nextDark = !dark;
    // Calls setDark with the supplied values.
    setDark(nextDark);
    // Calls savePreferences with the supplied values.
    savePreferences({ ...loadPreferences(), theme: nextDark ? 'dark' : 'light' });
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores focusMainContent for subsequent operations.
  const focusMainContent = (event: React.MouseEvent<HTMLAnchorElement>) => {
    // Computes and stores main for subsequent operations.
    const main = document.getElementById('main-content');
    // Checks this condition before running the nested branch.
    if (!main) return;
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Calls window.setTimeout with the supplied values.
    window.setTimeout(() => main.focus(), 0);
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores accountLabel for subsequent operations.
  const accountLabel = status === 'loading' ? t('connecting') : isGuest ? t('guest') : t('profile');

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="app-frame">
      {/* Renders the a interface element or component. */}
      <a className="skip-link" href="#main-content" onClick={focusMainContent}>
        {/* Executes this line as the next step in the surrounding logic. */}
        {t('skip')}
        {/* Closes the a interface element. */}
      </a>
      {/* Renders the header interface element or component. */}
      <header className="site-header">
        {/* Renders the Link interface element or component. */}
        <Link href="/" className="brand-link">
          {/* Renders the Logo interface element or component. */}
          <Logo />
          {/* Closes the Link interface element. */}
        </Link>
        {/* Renders the button interface element or component. */}
        <button
          /* Provides the className value to the surrounding call or element. */
          className="icon-button mobile-menu"
          /* Provides the type value to the surrounding call or element. */
          type="button"
          /* Provides the onClick value to the surrounding call or element. */
          onClick={() => setMenuOpen((open) => !open)}
          /* Executes this line as the next step in the surrounding logic. */
          aria-expanded={menuOpen}
          /* Executes this line as the next step in the surrounding logic. */
          aria-controls="primary-navigation"
          /* Executes this line as the next step in the surrounding logic. */
          aria-label={t('menu')}
          /* Closes the expression, call, or declaration started above. */
        >
          {/* Executes this line as the next step in the surrounding logic. */}
          {menuOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
          {/* Closes the button interface element. */}
        </button>
        {/* Renders the nav interface element or component. */}
        <nav
          /* Provides the id value to the surrounding call or element. */
          id="primary-navigation"
          /* Provides the className value to the surrounding call or element. */
          className={menuOpen ? 'primary-nav is-open' : 'primary-nav'}
          /* Executes this line as the next step in the surrounding logic. */
          aria-label={t('primaryNavigation')}
          /* Closes the expression, call, or declaration started above. */
        >
          {/* Executes this line as the next step in the surrounding logic. */}
          {navigation.map(([key, href]) => (
            // Renders the Link interface element or component.
            <Link
              /* Provides the key value to the surrounding call or element. */
              key={key}
              /* Provides the href value to the surrounding call or element. */
              href={href}
              /* Executes this line as the next step in the surrounding logic. */
              aria-current={pathname === href ? 'page' : undefined}
              /* Provides the onClick value to the surrounding call or element. */
              onClick={() => setMenuOpen(false)}
              /* Closes the expression, call, or declaration started above. */
            >
              {/* Executes this line as the next step in the surrounding logic. */}
              {t(key)}
              {/* Closes the Link interface element. */}
            </Link>
            // Closes the expression, call, or declaration started above.
          ))}
          {/* Closes the nav interface element. */}
        </nav>
        {/* Renders the div interface element or component. */}
        <div className="header-tools">
          {/* Renders the button interface element or component. */}
          <button
            /* Provides the className value to the surrounding call or element. */
            className="icon-button"
            /* Provides the type value to the surrounding call or element. */
            type="button"
            /* Provides the onClick value to the surrounding call or element. */
            onClick={handleTheme}
            /* Executes this line as the next step in the surrounding logic. */
            aria-label={dark ? t('lightMode') : t('darkMode')}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Executes this line as the next step in the surrounding logic. */}
            {dark ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
            {/* Closes the button interface element. */}
          </button>
          {/* Renders the Link interface element or component. */}
          <Link
            /* Provides the className value to the surrounding call or element. */
            className="icon-button"
            /* Provides the href value to the surrounding call or element. */
            href={pathname}
            /* Provides the locale value to the surrounding call or element. */
            locale={locale === 'en' ? 'zh-Hant' : 'en'}
            /* Executes this line as the next step in the surrounding logic. */
            aria-label={t('switchLocale')}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Renders the Languages interface element or component. */}
            <Languages aria-hidden="true" />
            {/* Closes the Link interface element. */}
          </Link>
          {/* Renders the Link interface element or component. */}
          <Link className="account-link" href="/profile" aria-label={accountLabel}>
            {/* Renders the UserRound interface element or component. */}
            <UserRound aria-hidden="true" />
            {/* Renders the span interface element or component. */}
            <span>{accountLabel}</span>
            {/* Closes the Link interface element. */}
          </Link>
          {/* Closes the div interface element. */}
        </div>
        {/* Closes the header interface element. */}
      </header>
      {/* Executes this line as the next step in the surrounding logic. */}
      {status === 'error' ? (
        // Renders the div interface element or component.
        <div className="global-status" role="alert">
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('authUnavailable')}
          {/* Closes the div interface element. */}
        </div>
      ) : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      null}
      {/* Renders the ServiceWorkerRegister interface element or component. */}
      <ServiceWorkerRegister />
      {/* Renders the main interface element or component. */}
      <main id="main-content" tabIndex={-1}>
        {/* Executes this line as the next step in the surrounding logic. */}
        {children}
        {/* Closes the main interface element. */}
      </main>
      {/* Renders the footer interface element or component. */}
      <footer className="site-footer">
        {/* Renders the div interface element or component. */}
        <div>
          {/* Renders the Logo interface element or component. */}
          <Logo compact />
          {/* Renders the span interface element or component. */}
          <span>{t('footerNote')}</span>
          {/* Closes the div interface element. */}
        </div>
        {/* Renders the nav interface element or component. */}
        <nav aria-label={t('legalNavigation')}>
          {/* Renders the Link interface element or component. */}
          <Link href="/guide">{t('rules')}</Link>
          {/* Renders the Link interface element or component. */}
          <Link href="/accessibility">{t('accessibility')}</Link>
          {/* Renders the Link interface element or component. */}
          <Link href="/privacy">{t('privacy')}</Link>
          {/* Renders the Link interface element or component. */}
          <Link href="/terms">{t('terms')}</Link>
          {/* Renders the Link interface element or component. */}
          <Link href="/support">{t('support')}</Link>
          {/* Closes the nav interface element. */}
        </nav>
        {/* Closes the footer interface element. */}
      </footer>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
