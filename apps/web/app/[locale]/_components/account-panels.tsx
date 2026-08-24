// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useLocale, useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useEffect, useState } from 'react';
// Imports the dependency used by this module.
import { useSession } from '@/components/session-provider';
// Imports the dependency used by this module.
import { Link, usePathname, useRouter } from '@/i18n/navigation';
// Imports the dependency used by this module.
import { API_ORIGIN, ApiError, useApi } from '@/lib/api';
// Imports the dependency used by this module.
import {
  // Supplies this item to the surrounding call or collection.
  defaultPreferences,
  // Supplies this item to the surrounding call or collection.
  loadPreferences,
  // Supplies this item to the surrounding call or collection.
  savePreferences,
  // Declares the Preferences data shape or implementation.
  type Preferences,
  // Executes this line as the next step in the surrounding logic.
} from '@/lib/preferences';

// Exports this declaration for use by other modules.
export function SettingsForm() {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Settings');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores pathname for subsequent operations.
  const pathname = usePathname();
  // Computes and stores router for subsequent operations.
  const router = useRouter();
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Executes this line as the next step in the surrounding logic.
  const [preferences, setPreferences] = useState(defaultPreferences);
  // Executes this line as the next step in the surrounding logic.
  const [publicLeaderboards, setPublicLeaderboards] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [preferencesReady, setPreferencesReady] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [profileReady, setProfileReady] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'idle' | 'saving' | 'saved'>('idle');
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Computes and stores frame for subsequent operations.
    const frame = requestAnimationFrame(() => {
      // Checks this condition before running the nested branch.
      if (!active) return;
      // Calls setPreferences with the supplied values.
      setPreferences(loadPreferences());
      // Calls setPreferencesReady with the supplied values.
      setPreferencesReady(true);
      // Closes the expression, call, or declaration started above.
    });
    // Executes this line as the next step in the surrounding logic.
    api<{ publicLeaderboards: boolean }>('/v1/me/profile')
      // Begins the nested block or object completed below.
      .then((profile) => {
        // Checks this condition before running the nested branch.
        if (active) setPublicLeaderboards(profile.publicLeaderboards);
        // Closes the expression, call, or declaration started above.
      })
      // Executes this line as the next step in the surrounding logic.
      .catch(() => undefined)
      // Begins the nested block or object completed below.
      .finally(() => {
        // Checks this condition before running the nested branch.
        if (active) setProfileReady(true);
        // Closes the expression, call, or declaration started above.
      });
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Calls cancelAnimationFrame with the supplied values.
      cancelAnimationFrame(frame);
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api]);

  // Computes and stores update for subsequent operations.
  const update = <K extends keyof Preferences>(key: K, value: Preferences[K]) => {
    // Calls setState with the supplied values.
    setState('idle');
    // Calls setPreferences with the supplied values.
    setPreferences((current) => ({ ...current, [key]: value }));
    // Closes the expression, call, or declaration started above.
  };
  // Computes and stores save for subsequent operations.
  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Checks this condition before running the nested branch.
    if (!preferencesReady || !profileReady) return;
    // Calls setState with the supplied values.
    setState('saving');
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Calls savePreferences with the supplied values.
      savePreferences(preferences);
      // Waits for this asynchronous operation to complete.
      await api('/v1/me/profile', {
        // Defines the method field in the surrounding object or type.
        method: 'PATCH',
        // Defines the body field in the surrounding object or type.
        body: JSON.stringify({ publicLeaderboards }),
        // Closes the expression, call, or declaration started above.
      });
      // Calls setState with the supplied values.
      setState('saved');
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('saveError'));
      // Calls setState with the supplied values.
      setState('idle');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the form interface element or component.
    <form
      /* Provides the className value to the surrounding call or element. */
      className="form-stack"
      /* Executes this line as the next step in the surrounding logic. */
      aria-busy={!preferencesReady || !profileReady}
      /* Provides the onSubmit value to the surrounding call or element. */
      onSubmit={(event) => void save(event)}
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Renders the fieldset interface element or component. */}
      <fieldset className="panel choice-group" disabled={!preferencesReady}>
        {/* Renders the legend interface element or component. */}
        <legend>{t('appearance')}</legend>
        {/* Renders the label interface element or component. */}
        <label className="field">
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('theme')}
          {/* Renders the select interface element or component. */}
          <select
            /* Provides the name value to the surrounding call or element. */
            name="theme"
            /* Provides the autoComplete value to the surrounding call or element. */
            autoComplete="off"
            /* Provides the value value to the surrounding call or element. */
            value={preferences.theme}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => update('theme', event.target.value as Preferences['theme'])}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Renders the option interface element or component. */}
            <option value="system">{t('system')}</option>
            {/* Renders the option interface element or component. */}
            <option value="light">{t('light')}</option>
            {/* Renders the option interface element or component. */}
            <option value="dark">{t('dark')}</option>
            {/* Closes the select interface element. */}
          </select>
          {/* Closes the label interface element. */}
        </label>
        {/* Renders the label interface element or component. */}
        <label className="field">
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('pegStyle')}
          {/* Renders the select interface element or component. */}
          <select
            /* Provides the name value to the surrounding call or element. */
            name="peg-style"
            /* Provides the autoComplete value to the surrounding call or element. */
            autoComplete="off"
            /* Provides the value value to the surrounding call or element. */
            value={preferences.pegStyle}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => update('pegStyle', event.target.value as Preferences['pegStyle'])}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Renders the option interface element or component. */}
            <option value="symbols">{t('symbols')}</option>
            {/* Renders the option interface element or component. */}
            <option value="patterns">{t('patterns')}</option>
            {/* Renders the option interface element or component. */}
            <option value="highContrast">{t('highContrast')}</option>
            {/* Closes the select interface element. */}
          </select>
          {/* Closes the label interface element. */}
        </label>
        {/* Renders the label interface element or component. */}
        <label className="check-row">
          {/* Renders the input interface element or component. */}
          <input
            /* Provides the type value to the surrounding call or element. */
            type="checkbox"
            /* Provides the name value to the surrounding call or element. */
            name="reduced-motion"
            /* Provides the checked value to the surrounding call or element. */
            checked={preferences.reducedMotion}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => update('reducedMotion', event.target.checked)}
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Renders the span interface element or component. */}
          <span>{t('motion')}</span>
          {/* Closes the label interface element. */}
        </label>
        {/* Renders the label interface element or component. */}
        <label className="check-row">
          {/* Renders the input interface element or component. */}
          <input
            /* Provides the type value to the surrounding call or element. */
            type="checkbox"
            /* Provides the name value to the surrounding call or element. */
            name="sound"
            /* Provides the checked value to the surrounding call or element. */
            checked={preferences.sound}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => update('sound', event.target.checked)}
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Renders the span interface element or component. */}
          <span>
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('sound')}
            {/* Renders the small interface element or component. */}
            <small>{t('soundHint')}</small>
            {/* Closes the span interface element. */}
          </span>
          {/* Closes the label interface element. */}
        </label>
        {/* Closes the fieldset interface element. */}
      </fieldset>
      {/* Renders the fieldset interface element or component. */}
      <fieldset className="panel choice-group">
        {/* Renders the legend interface element or component. */}
        <legend>{t('language')}</legend>
        {/* Renders the div interface element or component. */}
        <div className="segmented-options">
          {/* Renders the label interface element or component. */}
          <label>
            {/* Renders the input interface element or component. */}
            <input
              /* Provides the type value to the surrounding call or element. */
              type="radio"
              /* Provides the name value to the surrounding call or element. */
              name="locale"
              /* Provides the checked value to the surrounding call or element. */
              checked={locale === 'en'}
              /* Provides the onChange value to the surrounding call or element. */
              onChange={() => router.replace(pathname, { locale: 'en' })}
              /* Executes this line as the next step in the surrounding logic. */
            />
            {/* Renders the span interface element or component. */}
            <span>{t('english')}</span>
            {/* Closes the label interface element. */}
          </label>
          {/* Renders the label interface element or component. */}
          <label>
            {/* Renders the input interface element or component. */}
            <input
              /* Provides the type value to the surrounding call or element. */
              type="radio"
              /* Provides the name value to the surrounding call or element. */
              name="locale"
              /* Provides the checked value to the surrounding call or element. */
              checked={locale === 'zh-Hant'}
              /* Provides the onChange value to the surrounding call or element. */
              onChange={() => router.replace(pathname, { locale: 'zh-Hant' })}
              /* Executes this line as the next step in the surrounding logic. */
            />
            {/* Renders the span interface element or component. */}
            <span>{t('traditionalChinese')}</span>
            {/* Closes the label interface element. */}
          </label>
          {/* Closes the div interface element. */}
        </div>
        {/* Renders the p interface element or component. */}
        <p className="quiet-note">{t('timezone')}</p>
        {/* Closes the fieldset interface element. */}
      </fieldset>
      {/* Renders the fieldset interface element or component. */}
      <fieldset className="panel choice-group" disabled={!preferencesReady || !profileReady}>
        {/* Renders the legend interface element or component. */}
        <legend>{t('privacy')}</legend>
        {/* Renders the label interface element or component. */}
        <label className="check-row">
          {/* Renders the input interface element or component. */}
          <input
            /* Provides the type value to the surrounding call or element. */
            type="checkbox"
            /* Provides the name value to the surrounding call or element. */
            name="analytics"
            /* Provides the checked value to the surrounding call or element. */
            checked={preferences.analytics}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => update('analytics', event.target.checked)}
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Renders the span interface element or component. */}
          <span>
            {/* Executes this line as the next step in the surrounding logic. */}
            {t('analytics')}
            {/* Renders the small interface element or component. */}
            <small>{t('analyticsHint')}</small>
            {/* Closes the span interface element. */}
          </span>
          {/* Closes the label interface element. */}
        </label>
        {/* Renders the label interface element or component. */}
        <label className="check-row">
          {/* Renders the input interface element or component. */}
          <input
            /* Provides the type value to the surrounding call or element. */
            type="checkbox"
            /* Provides the name value to the surrounding call or element. */
            name="public-leaderboards"
            /* Provides the checked value to the surrounding call or element. */
            checked={publicLeaderboards}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => setPublicLeaderboards(event.target.checked)}
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Renders the span interface element or component. */}
          <span>{t('leaderboards')}</span>
          {/* Closes the label interface element. */}
        </label>
        {/* Closes the fieldset interface element. */}
      </fieldset>
      {/* Executes this line as the next step in the surrounding logic. */}
      {error ? (
        // Renders the p interface element or component.
        <p className="inline-error" role="alert">
          {/* Executes this line as the next step in the surrounding logic. */}
          {error}
          {/* Closes the p interface element. */}
        </p>
      ) : // Executes this line as the next step in the surrounding logic.
      null}
      {/* Renders the button interface element or component. */}
      <button
        /* Provides the className value to the surrounding call or element. */
        className="button primary"
        /* Provides the disabled value to the surrounding call or element. */
        disabled={!preferencesReady || !profileReady || state === 'saving'}
        /* Closes the expression, call, or declaration started above. */
      >
        {/* Executes this line as the next step in the surrounding logic. */}
        {state === 'saving' ? tc('saving') : state === 'saved' ? tc('saved') : tc('save')}
        {/* Closes the button interface element. */}
      </button>
      {/* Closes the form interface element. */}
    </form>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function AuthPanel({
  // Provides the callbackError value to the surrounding call or element.
  callbackError = null,
  // Begins the nested block or object completed below.
}: {
  // Executes this line as the next step in the surrounding logic.
  callbackError?: 'configuration' | 'invalid' | null;
  // Begins the nested block or object completed below.
}) {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Auth');
  // Executes this line as the next step in the surrounding logic.
  const { status, isGuest, sendMagicLink } = useSession();
  // Executes this line as the next step in the surrounding logic.
  const [email, setEmail] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'idle' | 'sending' | 'sent'>('idle');
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);
  // Computes and stores submit for subsequent operations.
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Calls setState with the supplied values.
    setState('sending');
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Waits for this asynchronous operation to complete.
      await sendMagicLink(email);
      // Calls setState with the supplied values.
      setState('sent');
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('error'));
      // Calls setState with the supplied values.
      setState('idle');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="split-layout">
      {/* Renders the section interface element or component. */}
      <section className="panel">
        {/* Renders the h2 interface element or component. */}
        <h2>{t('guest')}</h2>
        {/* Renders the p interface element or component. */}
        <p>{t('privacy')}</p>
        {/* Renders the Link interface element or component. */}
        <Link className="button primary" href="/play" aria-disabled={status === 'loading'}>
          {/* Executes this line as the next step in the surrounding logic. */}
          {status === 'loading' ? t('guestCreating') : t('guest')}
          {/* Closes the Link interface element. */}
        </Link>
        {/* Closes the section interface element. */}
      </section>
      {/* Renders the form interface element or component. */}
      <form className="panel form-stack" onSubmit={(event) => void submit(event)}>
        {/* Renders the h2 interface element or component. */}
        <h2>{t('magicLink')}</h2>
        {/* Executes this line as the next step in the surrounding logic. */}
        {callbackError ? (
          // Renders the p interface element or component.
          <p className="inline-error" role="alert">
            {/* Executes this line as the next step in the surrounding logic. */}
            {t(callbackError === 'configuration' ? 'configurationError' : 'invalidCallback')}
            {/* Closes the p interface element. */}
          </p>
        ) : // Executes this line as the next step in the surrounding logic.
        null}
        {/* Executes this line as the next step in the surrounding logic. */}
        {state === 'sent' ? (
          // Renders the div interface element or component.
          <div role="status">
            {/* Renders the h3 interface element or component. */}
            <h3>{t('sentTitle')}</h3>
            {/* Renders the p interface element or component. */}
            <p>{t('sentBody')}</p>
            {/* Closes the div interface element. */}
          </div>
        ) : (
          // Executes this line as the next step in the surrounding logic.
          // Starts a JSX fragment that groups the following interface elements.
          <>
            {/* Renders the label interface element or component. */}
            <label className="field">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('email')}
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the type value to the surrounding call or element. */
                type="email"
                /* Provides the name value to the surrounding call or element. */
                name="email"
                /* Provides the autoComplete value to the surrounding call or element. */
                autoComplete="email"
                /* Provides the spellCheck value to the surrounding call or element. */
                spellCheck={false}
                /* Executes this line as the next step in the surrounding logic. */
                required
                /* Provides the value value to the surrounding call or element. */
                value={email}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={(event) => setEmail(event.target.value)}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Closes the label interface element. */}
            </label>
            {/* Renders the button interface element or component. */}
            <button className="button secondary" disabled={state === 'sending'}>
              {/* Executes this line as the next step in the surrounding logic. */}
              {state === 'sending' ? t('sending') : t('magicLink')}
              {/* Closes the button interface element. */}
            </button>
            {/* Closes the JSX fragment started above. */}
          </>
          // Closes the expression, call, or declaration started above.
        )}
        {/* Executes this line as the next step in the surrounding logic. */}
        {error ? (
          // Renders the p interface element or component.
          <p className="inline-error" role="alert">
            {/* Executes this line as the next step in the surrounding logic. */}
            {error}
            {/* Closes the p interface element. */}
          </p>
        ) : // Executes this line as the next step in the surrounding logic.
        null}
        {/* Executes this line as the next step in the surrounding logic. */}
        {!isGuest ? <Link href="/profile">{t('continue')}</Link> : null}
        {/* Closes the form interface element. */}
      </form>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function AccountPanel() {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Account');
  // Executes this line as the next step in the surrounding logic.
  const { getAccessToken, isGuest, signOut } = useSession();
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Computes and stores router for subsequent operations.
  const router = useRouter();
  // Executes this line as the next step in the surrounding logic.
  const [confirmation, setConfirmation] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'idle' | 'exporting' | 'deleting'>('idle');
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [requiresRecentAuth, setRequiresRecentAuth] = useState(false);
  // Computes and stores exportData for subsequent operations.
  const exportData = async () => {
    // Calls setState with the supplied values.
    setState('exporting');
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores token for subsequent operations.
      const token = await getAccessToken();
      // Computes and stores response for subsequent operations.
      const response = await fetch(`${API_ORIGIN}/v1/me/export`, {
        // Defines the headers field in the surrounding object or type.
        headers: { Authorization: `Bearer ${token}` },
        // Closes the expression, call, or declaration started above.
      });
      // Checks this condition before running the nested branch.
      if (!response.ok) throw new Error('EXPORT_FAILED');
      // Computes and stores blob for subsequent operations.
      const blob = await response.blob();
      // Computes and stores url for subsequent operations.
      const url = URL.createObjectURL(blob);
      // Computes and stores link for subsequent operations.
      const link = document.createElement('a');
      // Executes this line as the next step in the surrounding logic.
      link.href = url;
      // Executes this line as the next step in the surrounding logic.
      link.download = 'cipherboard-data.zip';
      // Calls link.click with the supplied values.
      link.click();
      // Calls URL.revokeObjectURL with the supplied values.
      URL.revokeObjectURL(url);
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('deleteError'));
      // Runs cleanup regardless of the protected result.
    } finally {
      // Calls setState with the supplied values.
      setState('idle');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };
  // Computes and stores remove for subsequent operations.
  const remove = async (event: React.FormEvent<HTMLFormElement>) => {
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Checks this condition before running the nested branch.
    if (confirmation !== t('deletePhrase')) return;
    // Calls setState with the supplied values.
    setState('deleting');
    // Calls setError with the supplied values.
    setError(null);
    // Calls setRequiresRecentAuth with the supplied values.
    setRequiresRecentAuth(false);
    // Starts an operation whose expected failures are handled below.
    try {
      // Waits for this asynchronous operation to complete.
      await api('/v1/me', { method: 'DELETE', body: JSON.stringify({ confirmation: 'DELETE' }) });
      // Waits for this asynchronous operation to complete.
      await signOut();
      // Calls router.replace with the supplied values.
      router.replace('/');
      // Handles a failure from the protected operation.
    } catch (caught) {
      // Computes and stores recentAuthRequired for subsequent operations.
      const recentAuthRequired =
        // Executes this line as the next step in the surrounding logic.
        caught instanceof ApiError &&
        // Executes this line as the next step in the surrounding logic.
        (caught.status === 401 || caught.body.code === 'RECENT_AUTH_REQUIRED');
      // Calls setRequiresRecentAuth with the supplied values.
      setRequiresRecentAuth(recentAuthRequired);
      // Calls setError with the supplied values.
      setError(t(recentAuthRequired ? 'recentAuthRequired' : 'deleteError'));
      // Calls setState with the supplied values.
      setState('idle');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };
  // Checks this condition before running the nested branch.
  if (isGuest)
    // Returns this result to the caller and ends the current function.
    return (
      // Renders the section interface element or component.
      <section className="panel notice">
        {/* Renders the h2 interface element or component. */}
        <h2>{t('upgradeTitle')}</h2>
        {/* Renders the p interface element or component. */}
        <p>{t('upgradeBody')}</p>
        {/* Renders the Link interface element or component. */}
        <Link className="button primary" href="/auth">
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('upgradeAction')}
          {/* Closes the Link interface element. */}
        </Link>
        {/* Closes the section interface element. */}
      </section>
      // Closes the expression, call, or declaration started above.
    );
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="content-stack">
      {/* Renders the section interface element or component. */}
      <section className="panel">
        {/* Renders the h2 interface element or component. */}
        <h2>{t('exportTitle')}</h2>
        {/* Renders the p interface element or component. */}
        <p>{t('exportBody')}</p>
        {/* Renders the button interface element or component. */}
        <button
          /* Provides the className value to the surrounding call or element. */
          className="button secondary"
          /* Provides the type value to the surrounding call or element. */
          type="button"
          /* Provides the disabled value to the surrounding call or element. */
          disabled={state !== 'idle'}
          /* Provides the onClick value to the surrounding call or element. */
          onClick={() => void exportData()}
          /* Closes the expression, call, or declaration started above. */
        >
          {/* Executes this line as the next step in the surrounding logic. */}
          {state === 'exporting' ? t('exporting') : t('export')}
          {/* Closes the button interface element. */}
        </button>
        {/* Closes the section interface element. */}
      </section>
      {/* Renders the section interface element or component. */}
      <section className="panel">
        {/* Renders the h2 interface element or component. */}
        <h2>{t('signOut')}</h2>
        {/* Renders the button interface element or component. */}
        <button className="button secondary" type="button" onClick={() => void signOut()}>
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('signOut')}
          {/* Closes the button interface element. */}
        </button>
        {/* Closes the section interface element. */}
      </section>
      {/* Renders the form interface element or component. */}
      <form className="panel form-stack danger-zone" onSubmit={(event) => void remove(event)}>
        {/* Renders the h2 interface element or component. */}
        <h2>{t('deleteTitle')}</h2>
        {/* Renders the p interface element or component. */}
        <p>{t('deleteBody')}</p>
        {/* Renders the p interface element or component. */}
        <p className="quiet-note">{t('deleteWarning')}</p>
        {/* Renders the label interface element or component. */}
        <label className="field">
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('deleteConfirm')}
          {/* Renders the input interface element or component. */}
          <input
            /* Provides the name value to the surrounding call or element. */
            name="delete-confirmation"
            /* Provides the spellCheck value to the surrounding call or element. */
            spellCheck={false}
            /* Provides the value value to the surrounding call or element. */
            value={confirmation}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => setConfirmation(event.target.value)}
            /* Provides the autoComplete value to the surrounding call or element. */
            autoComplete="off"
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Closes the label interface element. */}
        </label>
        {/* Renders the button interface element or component. */}
        <button
          /* Provides the className value to the surrounding call or element. */
          className="button danger"
          /* Provides the disabled value to the surrounding call or element. */
          disabled={confirmation !== t('deletePhrase') || state !== 'idle'}
          /* Closes the expression, call, or declaration started above. */
        >
          {/* Executes this line as the next step in the surrounding logic. */}
          {state === 'deleting' ? t('deleting') : t('deleteAction')}
          {/* Closes the button interface element. */}
        </button>
        {/* Executes this line as the next step in the surrounding logic. */}
        {error ? (
          // Renders the div interface element or component.
          <div className="inline-error" role="alert">
            {/* Renders the p interface element or component. */}
            <p>{error}</p>
            {/* Executes this line as the next step in the surrounding logic. */}
            {requiresRecentAuth ? (
              // Renders the Link interface element or component.
              <Link className="button secondary" href="/auth">
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('signInAgain')}
                {/* Closes the Link interface element. */}
              </Link>
            ) : // Executes this line as the next step in the surrounding logic.
            null}
            {/* Closes the div interface element. */}
          </div>
        ) : // Executes this line as the next step in the surrounding logic.
        null}
        {/* Closes the form interface element. */}
      </form>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function SupportForm() {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Support');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Executes this line as the next step in the surrounding logic.
  const [topic, setTopic] = useState('gameplay');
  // Executes this line as the next step in the surrounding logic.
  const [email, setEmail] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [message, setMessage] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'idle' | 'sending' | 'sent'>('idle');
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);
  // Computes and stores submit for subsequent operations.
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Calls setState with the supplied values.
    setState('sending');
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Waits for this asynchronous operation to complete.
      await api('/v1/support', {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Defines the body field in the surrounding object or type.
        body: JSON.stringify({ topic, replyEmail: email, message }),
        // Closes the expression, call, or declaration started above.
      });
      // Calls setState with the supplied values.
      setState('sent');
      // Calls setMessage with the supplied values.
      setMessage('');
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('error'));
      // Calls setState with the supplied values.
      setState('idle');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };
  // Computes and stores topics for subsequent operations.
  const topics = [
    // Supplies this item to the surrounding call or collection.
    ['gameplay', 'gameplay'],
    // Supplies this item to the surrounding call or collection.
    ['account', 'account'],
    // Supplies this item to the surrounding call or collection.
    ['accessibility', 'accessibility'],
    // Supplies this item to the surrounding call or collection.
    ['privacy', 'privacy'],
    // Supplies this item to the surrounding call or collection.
    ['safety', 'safety'],
    // Supplies this item to the surrounding call or collection.
    ['other', 'other'],
    // Executes this line as the next step in the surrounding logic.
  ] as const;
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the form interface element or component.
    <form className="panel form-stack" onSubmit={(event) => void submit(event)}>
      {/* Executes this line as the next step in the surrounding logic. */}
      {state === 'sent' ? <p role="status">{t('success')}</p> : null}
      {/* Renders the label interface element or component. */}
      <label className="field">
        {/* Executes this line as the next step in the surrounding logic. */}
        {t('topic')}
        {/* Renders the select interface element or component. */}
        <select
          /* Provides the name value to the surrounding call or element. */
          name="topic"
          /* Provides the autoComplete value to the surrounding call or element. */
          autoComplete="off"
          /* Provides the value value to the surrounding call or element. */
          value={topic}
          /* Provides the onChange value to the surrounding call or element. */
          onChange={(event) => setTopic(event.target.value)}
          /* Closes the expression, call, or declaration started above. */
        >
          {/* Executes this line as the next step in the surrounding logic. */}
          {topics.map(([value, label]) => (
            // Renders the option interface element or component.
            <option key={value} value={value}>
              {/* Executes this line as the next step in the surrounding logic. */}
              {t(label)}
              {/* Closes the option interface element. */}
            </option>
            // Closes the expression, call, or declaration started above.
          ))}
          {/* Closes the select interface element. */}
        </select>
        {/* Closes the label interface element. */}
      </label>
      {/* Renders the label interface element or component. */}
      <label className="field">
        {/* Executes this line as the next step in the surrounding logic. */}
        {t('email')}
        {/* Renders the input interface element or component. */}
        <input
          /* Provides the type value to the surrounding call or element. */
          type="email"
          /* Provides the name value to the surrounding call or element. */
          name="email"
          /* Provides the autoComplete value to the surrounding call or element. */
          autoComplete="email"
          /* Provides the spellCheck value to the surrounding call or element. */
          spellCheck={false}
          /* Executes this line as the next step in the surrounding logic. */
          required
          /* Provides the value value to the surrounding call or element. */
          value={email}
          /* Provides the onChange value to the surrounding call or element. */
          onChange={(event) => setEmail(event.target.value)}
          /* Executes this line as the next step in the surrounding logic. */
        />
        {/* Closes the label interface element. */}
      </label>
      {/* Renders the label interface element or component. */}
      <label className="field">
        {/* Executes this line as the next step in the surrounding logic. */}
        {t('message')}
        {/* Renders the textarea interface element or component. */}
        <textarea
          /* Provides the name value to the surrounding call or element. */
          name="message"
          /* Provides the autoComplete value to the surrounding call or element. */
          autoComplete="off"
          /* Executes this line as the next step in the surrounding logic. */
          required
          /* Provides the maxLength value to the surrounding call or element. */
          maxLength={4000}
          /* Provides the value value to the surrounding call or element. */
          value={message}
          /* Provides the onChange value to the surrounding call or element. */
          onChange={(event) => setMessage(event.target.value)}
          /* Executes this line as the next step in the surrounding logic. */
          aria-describedby="support-hint"
          /* Executes this line as the next step in the surrounding logic. */
        />
        {/* Closes the label interface element. */}
      </label>
      {/* Renders the small interface element or component. */}
      <small id="support-hint">{t('messageHint')}</small>
      {/* Executes this line as the next step in the surrounding logic. */}
      {error ? (
        // Renders the p interface element or component.
        <p className="inline-error" role="alert">
          {/* Executes this line as the next step in the surrounding logic. */}
          {error}
          {/* Closes the p interface element. */}
        </p>
      ) : // Executes this line as the next step in the surrounding logic.
      null}
      {/* Renders the button interface element or component. */}
      <button className="button primary" disabled={state === 'sending'}>
        {/* Executes this line as the next step in the surrounding logic. */}
        {state === 'sending' ? t('sending') : t('send')}
        {/* Closes the button interface element. */}
      </button>
      {/* Closes the form interface element. */}
    </form>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
