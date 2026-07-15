'use client';

import { Languages, Menu, Moon, Sun, UserRound, X } from 'lucide-react';
import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { Link, usePathname } from '@/i18n/navigation';
import { applyPreferences, loadPreferences, savePreferences } from '@/lib/preferences';
import { Logo } from './logo';
import { ServiceWorkerRegister } from './service-worker-register';
import { useSession } from './session-provider';

const navigation = [
  ['play', '/play'],
  ['daily', '/daily'],
  ['challenges', '/challenges/new'],
  ['rooms', '/rooms'],
  ['leaderboards', '/leaderboards'],
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const t = useTranslations('App');
  const locale = useLocale();
  const pathname = usePathname();
  const { status, isGuest } = useSession();
  const [menuOpen, setMenuOpen] = useState(false);
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const colourScheme = matchMedia('(prefers-color-scheme: dark)');
    const syncPreferences = () => {
      const preferences = loadPreferences();
      const nextDark =
        preferences.theme === 'dark' || (preferences.theme === 'system' && colourScheme.matches);
      setDark(nextDark);
      applyPreferences(preferences);
    };
    const handleColourScheme = () => {
      if (loadPreferences().theme === 'system') syncPreferences();
    };
    const frame = requestAnimationFrame(syncPreferences);
    window.addEventListener('cipherboard:preferences-changed', syncPreferences);
    colourScheme.addEventListener('change', handleColourScheme);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('cipherboard:preferences-changed', syncPreferences);
      colourScheme.removeEventListener('change', handleColourScheme);
    };
  }, []);

  const handleTheme = () => {
    const nextDark = !dark;
    setDark(nextDark);
    savePreferences({ ...loadPreferences(), theme: nextDark ? 'dark' : 'light' });
  };

  const focusMainContent = (event: React.MouseEvent<HTMLAnchorElement>) => {
    const main = document.getElementById('main-content');
    if (!main) return;
    event.preventDefault();
    window.setTimeout(() => main.focus(), 0);
  };

  const accountLabel = status === 'loading' ? t('connecting') : isGuest ? t('guest') : t('profile');

  return (
    <div className="app-frame">
      <a className="skip-link" href="#main-content" onClick={focusMainContent}>
        {t('skip')}
      </a>
      <header className="site-header">
        <Link href="/" className="brand-link">
          <Logo />
        </Link>
        <button
          className="icon-button mobile-menu"
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          aria-expanded={menuOpen}
          aria-controls="primary-navigation"
          aria-label={t('menu')}
        >
          {menuOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
        </button>
        <nav
          id="primary-navigation"
          className={menuOpen ? 'primary-nav is-open' : 'primary-nav'}
          aria-label={t('primaryNavigation')}
        >
          {navigation.map(([key, href]) => (
            <Link
              key={key}
              href={href}
              aria-current={pathname === href ? 'page' : undefined}
              onClick={() => setMenuOpen(false)}
            >
              {t(key)}
            </Link>
          ))}
        </nav>
        <div className="header-tools">
          <button
            className="icon-button"
            type="button"
            onClick={handleTheme}
            aria-label={dark ? t('lightMode') : t('darkMode')}
          >
            {dark ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
          </button>
          <Link
            className="icon-button"
            href={pathname}
            locale={locale === 'en' ? 'zh-Hant' : 'en'}
            aria-label={t('switchLocale')}
          >
            <Languages aria-hidden="true" />
          </Link>
          <Link className="account-link" href="/profile" aria-label={accountLabel}>
            <UserRound aria-hidden="true" />
            <span>{accountLabel}</span>
          </Link>
        </div>
      </header>
      {status === 'error' ? (
        <div className="global-status" role="alert">
          {t('authUnavailable')}
        </div>
      ) : null}
      <ServiceWorkerRegister />
      <main id="main-content" tabIndex={-1}>
        {children}
      </main>
      <footer className="site-footer">
        <div>
          <Logo compact />
          <span>{t('footerNote')}</span>
        </div>
        <nav aria-label={t('legalNavigation')}>
          <Link href="/guide">{t('rules')}</Link>
          <Link href="/accessibility">{t('accessibility')}</Link>
          <Link href="/privacy">{t('privacy')}</Link>
          <Link href="/terms">{t('terms')}</Link>
          <Link href="/support">{t('support')}</Link>
        </nav>
      </footer>
    </div>
  );
}
