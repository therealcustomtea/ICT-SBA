'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { useSession } from '@/components/session-provider';
import { Link, usePathname, useRouter } from '@/i18n/navigation';
import { API_ORIGIN, ApiError, useApi } from '@/lib/api';
import {
  defaultPreferences,
  loadPreferences,
  savePreferences,
  type Preferences,
} from '@/lib/preferences';

export function SettingsForm() {
  const t = useTranslations('Settings');
  const tc = useTranslations('Common');
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const api = useApi();
  const [preferences, setPreferences] = useState(defaultPreferences);
  const [publicLeaderboards, setPublicLeaderboards] = useState(false);
  const [preferencesReady, setPreferencesReady] = useState(false);
  const [profileReady, setProfileReady] = useState(false);
  const [state, setState] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const frame = requestAnimationFrame(() => {
      if (!active) return;
      setPreferences(loadPreferences());
      setPreferencesReady(true);
    });
    api<{ publicLeaderboards: boolean }>('/v1/me/profile')
      .then((profile) => {
        if (active) setPublicLeaderboards(profile.publicLeaderboards);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setProfileReady(true);
      });
    return () => {
      active = false;
      cancelAnimationFrame(frame);
    };
  }, [api]);

  const update = <K extends keyof Preferences>(key: K, value: Preferences[K]) => {
    setState('idle');
    setPreferences((current) => ({ ...current, [key]: value }));
  };
  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!preferencesReady || !profileReady) return;
    setState('saving');
    setError(null);
    try {
      savePreferences(preferences);
      await api('/v1/me/profile', {
        method: 'PATCH',
        body: JSON.stringify({ publicLeaderboards }),
      });
      setState('saved');
    } catch {
      setError(t('saveError'));
      setState('idle');
    }
  };

  return (
    <form
      className="form-stack"
      aria-busy={!preferencesReady || !profileReady}
      onSubmit={(event) => void save(event)}
    >
      <fieldset className="panel choice-group" disabled={!preferencesReady}>
        <legend>{t('appearance')}</legend>
        <label className="field">
          {t('theme')}
          <select
            name="theme"
            autoComplete="off"
            value={preferences.theme}
            onChange={(event) => update('theme', event.target.value as Preferences['theme'])}
          >
            <option value="system">{t('system')}</option>
            <option value="light">{t('light')}</option>
            <option value="dark">{t('dark')}</option>
          </select>
        </label>
        <label className="field">
          {t('pegStyle')}
          <select
            name="peg-style"
            autoComplete="off"
            value={preferences.pegStyle}
            onChange={(event) => update('pegStyle', event.target.value as Preferences['pegStyle'])}
          >
            <option value="symbols">{t('symbols')}</option>
            <option value="patterns">{t('patterns')}</option>
            <option value="highContrast">{t('highContrast')}</option>
          </select>
        </label>
        <label className="check-row">
          <input
            type="checkbox"
            name="reduced-motion"
            checked={preferences.reducedMotion}
            onChange={(event) => update('reducedMotion', event.target.checked)}
          />
          <span>{t('motion')}</span>
        </label>
        <label className="check-row">
          <input
            type="checkbox"
            name="sound"
            checked={preferences.sound}
            onChange={(event) => update('sound', event.target.checked)}
          />
          <span>
            {t('sound')}
            <small>{t('soundHint')}</small>
          </span>
        </label>
      </fieldset>
      <fieldset className="panel choice-group">
        <legend>{t('language')}</legend>
        <div className="segmented-options">
          <label>
            <input
              type="radio"
              name="locale"
              checked={locale === 'en'}
              onChange={() => router.replace(pathname, { locale: 'en' })}
            />
            <span>{t('english')}</span>
          </label>
          <label>
            <input
              type="radio"
              name="locale"
              checked={locale === 'zh-Hant'}
              onChange={() => router.replace(pathname, { locale: 'zh-Hant' })}
            />
            <span>{t('traditionalChinese')}</span>
          </label>
        </div>
        <p className="quiet-note">{t('timezone')}</p>
      </fieldset>
      <fieldset className="panel choice-group" disabled={!preferencesReady || !profileReady}>
        <legend>{t('privacy')}</legend>
        <label className="check-row">
          <input
            type="checkbox"
            name="analytics"
            checked={preferences.analytics}
            onChange={(event) => update('analytics', event.target.checked)}
          />
          <span>
            {t('analytics')}
            <small>{t('analyticsHint')}</small>
          </span>
        </label>
        <label className="check-row">
          <input
            type="checkbox"
            name="public-leaderboards"
            checked={publicLeaderboards}
            onChange={(event) => setPublicLeaderboards(event.target.checked)}
          />
          <span>{t('leaderboards')}</span>
        </label>
      </fieldset>
      {error ? (
        <p className="inline-error" role="alert">
          {error}
        </p>
      ) : null}
      <button
        className="button primary"
        disabled={!preferencesReady || !profileReady || state === 'saving'}
      >
        {state === 'saving' ? tc('saving') : state === 'saved' ? tc('saved') : tc('save')}
      </button>
    </form>
  );
}

export function AuthPanel({
  callbackError = null,
}: {
  callbackError?: 'configuration' | 'invalid' | null;
}) {
  const t = useTranslations('Auth');
  const { status, isGuest, sendMagicLink } = useSession();
  const [email, setEmail] = useState('');
  const [state, setState] = useState<'idle' | 'sending' | 'sent'>('idle');
  const [error, setError] = useState<string | null>(null);
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setState('sending');
    setError(null);
    try {
      await sendMagicLink(email);
      setState('sent');
    } catch {
      setError(t('error'));
      setState('idle');
    }
  };
  return (
    <div className="split-layout">
      <section className="panel">
        <h2>{t('guest')}</h2>
        <p>{t('privacy')}</p>
        <Link className="button primary" href="/play" aria-disabled={status === 'loading'}>
          {status === 'loading' ? t('guestCreating') : t('guest')}
        </Link>
      </section>
      <form className="panel form-stack" onSubmit={(event) => void submit(event)}>
        <h2>{t('magicLink')}</h2>
        {callbackError ? (
          <p className="inline-error" role="alert">
            {t(callbackError === 'configuration' ? 'configurationError' : 'invalidCallback')}
          </p>
        ) : null}
        {state === 'sent' ? (
          <div role="status">
            <h3>{t('sentTitle')}</h3>
            <p>{t('sentBody')}</p>
          </div>
        ) : (
          <>
            <label className="field">
              {t('email')}
              <input
                type="email"
                name="email"
                autoComplete="email"
                spellCheck={false}
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <button className="button secondary" disabled={state === 'sending'}>
              {state === 'sending' ? t('sending') : t('magicLink')}
            </button>
          </>
        )}
        {error ? (
          <p className="inline-error" role="alert">
            {error}
          </p>
        ) : null}
        {!isGuest ? <Link href="/profile">{t('continue')}</Link> : null}
      </form>
    </div>
  );
}

export function AccountPanel() {
  const t = useTranslations('Account');
  const { getAccessToken, isGuest, signOut } = useSession();
  const api = useApi();
  const router = useRouter();
  const [confirmation, setConfirmation] = useState('');
  const [state, setState] = useState<'idle' | 'exporting' | 'deleting'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [requiresRecentAuth, setRequiresRecentAuth] = useState(false);
  const exportData = async () => {
    setState('exporting');
    setError(null);
    try {
      const token = await getAccessToken();
      const response = await fetch(`${API_ORIGIN}/v1/me/export`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('EXPORT_FAILED');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'cipherboard-data.zip';
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setError(t('deleteError'));
    } finally {
      setState('idle');
    }
  };
  const remove = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (confirmation !== t('deletePhrase')) return;
    setState('deleting');
    setError(null);
    setRequiresRecentAuth(false);
    try {
      await api('/v1/me', { method: 'DELETE', body: JSON.stringify({ confirmation: 'DELETE' }) });
      await signOut();
      router.replace('/');
    } catch (caught) {
      const recentAuthRequired =
        caught instanceof ApiError &&
        (caught.status === 401 || caught.body.code === 'RECENT_AUTH_REQUIRED');
      setRequiresRecentAuth(recentAuthRequired);
      setError(t(recentAuthRequired ? 'recentAuthRequired' : 'deleteError'));
      setState('idle');
    }
  };
  if (isGuest)
    return (
      <section className="panel notice">
        <h2>{t('upgradeTitle')}</h2>
        <p>{t('upgradeBody')}</p>
        <Link className="button primary" href="/auth">
          {t('upgradeAction')}
        </Link>
      </section>
    );
  return (
    <div className="content-stack">
      <section className="panel">
        <h2>{t('exportTitle')}</h2>
        <p>{t('exportBody')}</p>
        <button
          className="button secondary"
          type="button"
          disabled={state !== 'idle'}
          onClick={() => void exportData()}
        >
          {state === 'exporting' ? t('exporting') : t('export')}
        </button>
      </section>
      <section className="panel">
        <h2>{t('signOut')}</h2>
        <button className="button secondary" type="button" onClick={() => void signOut()}>
          {t('signOut')}
        </button>
      </section>
      <form className="panel form-stack danger-zone" onSubmit={(event) => void remove(event)}>
        <h2>{t('deleteTitle')}</h2>
        <p>{t('deleteBody')}</p>
        <p className="quiet-note">{t('deleteWarning')}</p>
        <label className="field">
          {t('deleteConfirm')}
          <input
            name="delete-confirmation"
            spellCheck={false}
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
            autoComplete="off"
          />
        </label>
        <button
          className="button danger"
          disabled={confirmation !== t('deletePhrase') || state !== 'idle'}
        >
          {state === 'deleting' ? t('deleting') : t('deleteAction')}
        </button>
        {error ? (
          <div className="inline-error" role="alert">
            <p>{error}</p>
            {requiresRecentAuth ? (
              <Link className="button secondary" href="/auth">
                {t('signInAgain')}
              </Link>
            ) : null}
          </div>
        ) : null}
      </form>
    </div>
  );
}

export function SupportForm() {
  const t = useTranslations('Support');
  const api = useApi();
  const [topic, setTopic] = useState('gameplay');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [state, setState] = useState<'idle' | 'sending' | 'sent'>('idle');
  const [error, setError] = useState<string | null>(null);
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setState('sending');
    setError(null);
    try {
      await api('/v1/support', {
        method: 'POST',
        body: JSON.stringify({ topic, replyEmail: email, message }),
      });
      setState('sent');
      setMessage('');
    } catch {
      setError(t('error'));
      setState('idle');
    }
  };
  const topics = [
    ['gameplay', 'gameplay'],
    ['account', 'account'],
    ['accessibility', 'accessibility'],
    ['privacy', 'privacy'],
    ['safety', 'safety'],
    ['other', 'other'],
  ] as const;
  return (
    <form className="panel form-stack" onSubmit={(event) => void submit(event)}>
      {state === 'sent' ? <p role="status">{t('success')}</p> : null}
      <label className="field">
        {t('topic')}
        <select
          name="topic"
          autoComplete="off"
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
        >
          {topics.map(([value, label]) => (
            <option key={value} value={value}>
              {t(label)}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        {t('email')}
        <input
          type="email"
          name="email"
          autoComplete="email"
          spellCheck={false}
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
      </label>
      <label className="field">
        {t('message')}
        <textarea
          name="message"
          autoComplete="off"
          required
          maxLength={4000}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          aria-describedby="support-hint"
        />
      </label>
      <small id="support-hint">{t('messageHint')}</small>
      {error ? (
        <p className="inline-error" role="alert">
          {error}
        </p>
      ) : null}
      <button className="button primary" disabled={state === 'sending'}>
        {state === 'sending' ? t('sending') : t('send')}
      </button>
    </form>
  );
}
