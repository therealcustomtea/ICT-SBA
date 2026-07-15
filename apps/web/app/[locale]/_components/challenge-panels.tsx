'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useEffect, useRef, useState } from 'react';
import { AsyncState } from '@/components/feature-page';
import { GameBoard } from '@/components/game-board';
import { type Challenge, type ChallengeResults, useApi } from '@/lib/api';
import { useProductAnalytics } from '@/lib/use-product-analytics';

const colourIds = ['R', 'B', 'G', 'Y', 'W', 'K', 'O', 'P', 'C', 'M'] as const;
const challengePresets = {
  easy: { colours: colourIds.slice(0, 5), length: 4, maxAttempts: 12, duplicates: false },
  normal: { colours: colourIds.slice(0, 6), length: 4, maxAttempts: 10, duplicates: true },
  hard: { colours: colourIds.slice(0, 8), length: 5, maxAttempts: 8, duplicates: true },
  expert: { colours: colourIds.slice(0, 10), length: 6, maxAttempts: 8, duplicates: true },
} as const;
const symbols: Record<string, string> = {
  R: '●',
  B: '◆',
  G: '▲',
  Y: '■',
  W: '○',
  K: '✚',
  O: '⬟',
  P: '✦',
  C: '⬢',
  M: '♥',
};
type OwnedChallenge = {
  id: string;
  title: string | null;
  showCreatorName: boolean;
  config: Challenge['config'];
  revoked: boolean;
  expiresAt: string;
  completedCount: number;
  createdAt: string;
};
type OwnedChallengesResponse = {
  items: OwnedChallenge[];
  page: number;
  pageSize: number;
  total: number;
};
const RESULTS_PAGE_SIZE = 10;

function ChallengeResultBoard({
  results,
  compact = false,
  onPageChange,
}: {
  results: ChallengeResults;
  compact?: boolean;
  onPageChange?: (page: number) => void;
}) {
  const locale = useLocale();
  const t = useTranslations('Challenges');
  const tg = useTranslations('Game');
  const tc = useTranslations('Common');
  const numberFormat = new Intl.NumberFormat(locale);
  const completedAtFormat = new Intl.DateTimeFormat(locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  return (
    <>
      <dl className={`rules-summary${compact ? ' compact-results' : ''}`}>
        <div>
          <dt>{t('completed')}</dt>
          <dd>{results.completedCount}</dd>
        </div>
        <div>
          <dt>{t('winRate')}</dt>
          <dd>{results.winRate}%</dd>
        </div>
        <div>
          <dt>{t('averageAttempts')}</dt>
          <dd>{results.averageAttempts ?? '—'}</dd>
        </div>
      </dl>
      {results.items.length ? (
        <>
          <p className="quiet-note">{t('resultsOrder')}</p>
          <div
            className="table-scroll challenge-results-table"
            role="region"
            aria-label={t('resultsTableRegion')}
            tabIndex={0}
          >
            <table>
              <caption className="sr-only">{t('resultsTitle')}</caption>
              <thead>
                <tr>
                  <th scope="col">{t('rank')}</th>
                  <th scope="col">{t('player')}</th>
                  <th scope="col">{t('result')}</th>
                  <th scope="col">{t('score')}</th>
                  <th scope="col">{t('attempts')}</th>
                  <th scope="col">{t('time')}</th>
                  <th scope="col">{t('completedAt')}</th>
                </tr>
              </thead>
              <tbody>
                {results.items.map((item) => {
                  const playerToken = item.playerLabel.startsWith('Breaker ')
                    ? item.playerLabel.slice('Breaker '.length)
                    : item.playerLabel;
                  const knownResult = [
                    'created',
                    'active',
                    'won',
                    'lost',
                    'abandoned',
                    'expired',
                  ].includes(item.result)
                    ? item.result
                    : null;
                  return (
                    <tr key={`${item.rank}-${item.playerLabel}`}>
                      <td>{item.rank}</td>
                      <th scope="row">{t('breakerLabel', { token: playerToken })}</th>
                      <td>
                        <span className={`status ${knownResult ?? 'muted'}`}>
                          {knownResult ? tg(`status.${knownResult}`) : tc('unavailable')}
                        </span>
                      </td>
                      <td>{numberFormat.format(item.score)}</td>
                      <td>
                        {t('attemptsOf', {
                          used: item.attemptsUsed,
                          maximum: item.maxAttempts,
                        })}
                      </td>
                      <td>
                        {item.elapsedSeconds === null
                          ? tc('unavailable')
                          : formatChallengeDuration(item.elapsedSeconds)}
                      </td>
                      <td>
                        <time dateTime={item.completedAt}>
                          {completedAtFormat.format(new Date(item.completedAt))}
                        </time>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {onPageChange && results.total > results.pageSize ? (
            <nav className="pagination" aria-label={t('resultsPage', { page: results.page })}>
              <button
                className="button secondary"
                type="button"
                disabled={results.page <= 1}
                onClick={() => onPageChange(Math.max(1, results.page - 1))}
              >
                {tc('previous')}
              </button>
              <span>{tc('page', { page: results.page })}</span>
              <button
                className="button secondary"
                type="button"
                disabled={results.page * results.pageSize >= results.total}
                onClick={() => onPageChange(results.page + 1)}
              >
                {tc('next')}
              </button>
            </nav>
          ) : null}
        </>
      ) : (
        <p className="quiet-note">{t('resultsEmpty')}</p>
      )}
    </>
  );
}

function formatChallengeDuration(seconds: number) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}

export function ChallengeCreator() {
  const locale = useLocale();
  const t = useTranslations('Challenges');
  const tp = useTranslations('Play');
  const tc = useTranslations('Common');
  const tg = useTranslations('Game');
  const api = useApi();
  const analytics = useProductAnalytics();
  const [difficulty, setDifficulty] = useState<'easy' | 'normal' | 'hard' | 'expert' | 'custom'>(
    'normal',
  );
  const [colourCount, setColourCount] = useState(6);
  const [codeLength, setCodeLength] = useState(4);
  const [maxAttempts, setMaxAttempts] = useState(10);
  const [duplicatesAllowed, setDuplicatesAllowed] = useState(true);
  const [title, setTitle] = useState('');
  const [showCreatorName, setShowCreatorName] = useState(true);
  const [manual, setManual] = useState(false);
  const [secret, setSecret] = useState<string[]>([]);
  const [created, setCreated] = useState<Challenge | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');
  const [results, setResults] = useState<ChallengeResults | null>(null);
  const [resultsError, setResultsError] = useState(false);
  const [resultsPage, setResultsPage] = useState(1);
  const [ownedChallenges, setOwnedChallenges] = useState<OwnedChallenge[]>([]);
  const [ownedState, setOwnedState] = useState<'loading' | 'error' | 'empty' | 'ready'>('loading');
  const [ownedPage, setOwnedPage] = useState(1);
  const [ownedTotal, setOwnedTotal] = useState(0);
  const [ownedResults, setOwnedResults] = useState<{
    challengeId: string;
    state: 'loading' | 'error' | 'ready';
    data: ChallengeResults | null;
  } | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [ownedActionErrorId, setOwnedActionErrorId] = useState<string | null>(null);
  const [renderedAt] = useState(Date.now);
  const creationKeyRef = useRef<string | null>(null);
  const selectedRules =
    difficulty === 'custom'
      ? {
          colours: colourIds.slice(0, colourCount),
          length: codeLength,
          maxAttempts,
          duplicates: duplicatesAllowed,
        }
      : challengePresets[difficulty];
  const invalidCustom = difficulty === 'custom' && !duplicatesAllowed && colourCount < codeLength;

  const loadOwnedChallenges = async () => {
    try {
      const response = await api<OwnedChallengesResponse>(
        `/v1/challenges/mine?page=${ownedPage}&page_size=20`,
      );
      setOwnedChallenges(response.items);
      setOwnedTotal(response.total);
      setOwnedState(response.items.length ? 'ready' : 'empty');
    } catch {
      setOwnedState('error');
    }
  };

  useEffect(() => {
    let active = true;
    api<OwnedChallengesResponse>(`/v1/challenges/mine?page=${ownedPage}&page_size=20`)
      .then((response) => {
        if (active) {
          setOwnedChallenges(response.items);
          setOwnedTotal(response.total);
          setOwnedState(response.items.length ? 'ready' : 'empty');
        }
      })
      .catch(() => {
        if (active) setOwnedState('error');
      });
    return () => {
      active = false;
    };
  }, [api, ownedPage]);

  useEffect(() => {
    if (!created?.id) return;
    let active = true;
    api<ChallengeResults>(
      `/v1/challenges/${encodeURIComponent(created.id)}/results?page=${resultsPage}&page_size=${RESULTS_PAGE_SIZE}`,
    )
      .then((value) => {
        if (active) setResults(value);
      })
      .catch(() => {
        if (active) setResultsError(true);
      });
    return () => {
      active = false;
    };
  }, [api, created?.id, resultsPage]);

  const create = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (invalidCustom || (manual && secret.length !== selectedRules.length)) return;
    setSubmitting(true);
    setError(null);
    try {
      creationKeyRef.current ??= crypto.randomUUID();
      const selection =
        difficulty === 'custom'
          ? {
              config: {
                colours: [...selectedRules.colours],
                codeLength: selectedRules.length,
                maxAttempts: selectedRules.maxAttempts,
                duplicatesAllowed: selectedRules.duplicates,
                codeMaker: manual ? 'human' : 'computer',
                visibility: 'shareable',
                ranked: false,
                timeBonusCap: 300,
              },
            }
          : { difficulty };
      const challenge = await api<Challenge>('/v1/challenges', {
        method: 'POST',
        body: JSON.stringify({
          ...selection,
          title: title || null,
          showCreatorName,
          idempotencyKey: creationKeyRef.current,
          ...(manual ? { secret } : {}),
        }),
      });
      setSecret([]);
      setResults(null);
      setResultsError(false);
      setResultsPage(1);
      setCreated(challenge);
      creationKeyRef.current = null;
      analytics('friend_challenge_created', { official: true, expiryBand: '30_days' });
      if (ownedPage === 1) void loadOwnedChallenges();
      else {
        setOwnedState('loading');
        setOwnedPage(1);
      }
    } catch {
      setError(t('createError'));
    } finally {
      setSubmitting(false);
    }
  };

  const shareUrl =
    created && typeof window !== 'undefined'
      ? `${window.location.origin}${window.location.pathname.replace('/new', `/${created.shareCode}`)}`
      : '';
  const copy = async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopyState('copied');
    } catch {
      setCopyState('error');
    }
  };
  const revoke = async () => {
    if (!created?.id || !confirm(t('revokeConfirm'))) return;
    try {
      await api<void>(`/v1/challenges/${encodeURIComponent(created.id)}`, { method: 'DELETE' });
      setCreated({ ...created, revoked: true });
      setOwnedChallenges((current) =>
        current.map((item) => (item.id === created.id ? { ...item, revoked: true } : item)),
      );
    } catch {
      setError(t('createError'));
    }
  };

  const viewOwnedResults = async (challengeId: string, page = 1) => {
    setOwnedResults({ challengeId, state: 'loading', data: null });
    try {
      const data = await api<ChallengeResults>(
        `/v1/challenges/${encodeURIComponent(challengeId)}/results?page=${page}&page_size=${RESULTS_PAGE_SIZE}`,
      );
      setOwnedResults({ challengeId, state: 'ready', data });
    } catch {
      setOwnedResults({ challengeId, state: 'error', data: null });
    }
  };

  const revokeOwned = async (challengeId: string) => {
    if (!confirm(t('revokeConfirm'))) return;
    setRevokingId(challengeId);
    setOwnedActionErrorId(null);
    try {
      await api<void>(`/v1/challenges/${encodeURIComponent(challengeId)}`, { method: 'DELETE' });
      setOwnedChallenges((current) =>
        current.map((item) => (item.id === challengeId ? { ...item, revoked: true } : item)),
      );
      if (created?.id === challengeId) setCreated({ ...created, revoked: true });
    } catch {
      setOwnedActionErrorId(challengeId);
    } finally {
      setRevokingId(null);
    }
  };

  const managementPanel = (
    <section className="panel challenge-management" aria-labelledby="my-challenges-heading">
      <div>
        <h2 id="my-challenges-heading">{t('mineTitle')}</h2>
        <p className="quiet-note">{t('mineIntro')}</p>
      </div>
      <AsyncState
        state={ownedState}
        loadingLabel={t('loadingMine')}
        errorLabel={t('mineError')}
        emptyLabel={t('mineEmpty')}
      >
        <ul className="challenge-management-list">
          {ownedChallenges.map((item) => {
            const expired = new Date(item.expiresAt).getTime() <= renderedAt;
            const statusKey = item.revoked
              ? 'statusRevoked'
              : expired
                ? 'statusExpired'
                : 'statusActive';
            const result = ownedResults?.challengeId === item.id ? ownedResults : null;
            return (
              <li key={item.id}>
                <div className="challenge-management-summary">
                  <div>
                    <h3>{item.title ?? t('untitled')}</h3>
                    <p>
                      <span className={`status ${item.revoked || expired ? 'muted' : 'success'}`}>
                        {t(statusKey)}
                      </span>{' '}
                      · {t('completedCount', { count: item.completedCount })}
                    </p>
                    <small>
                      {new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(
                        new Date(item.createdAt),
                      )}
                    </small>
                  </div>
                  <div className="button-row">
                    <button
                      className="button secondary"
                      type="button"
                      onClick={() => void viewOwnedResults(item.id)}
                    >
                      {t('viewResults')}
                    </button>
                    {!item.revoked && !expired ? (
                      <button
                        className="button danger"
                        type="button"
                        disabled={revokingId === item.id}
                        onClick={() => void revokeOwned(item.id)}
                      >
                        {revokingId === item.id ? t('revoking') : t('revoke')}
                      </button>
                    ) : null}
                  </div>
                </div>
                {ownedActionErrorId === item.id ? (
                  <p className="inline-error" role="alert">
                    {t('revokeError')}
                  </p>
                ) : null}
                {result?.state === 'loading' ? (
                  <p role="status">{t('loadingResults')}</p>
                ) : result?.state === 'error' ? (
                  <p className="inline-error" role="alert">
                    {t('resultsError')}
                  </p>
                ) : result?.data ? (
                  <section aria-labelledby={`challenge-results-${item.id}`}>
                    <h4 id={`challenge-results-${item.id}`}>{t('resultsTitle')}</h4>
                    <ChallengeResultBoard
                      compact
                      results={result.data}
                      onPageChange={(page) => void viewOwnedResults(item.id, page)}
                    />
                  </section>
                ) : null}
              </li>
            );
          })}
        </ul>
        {ownedTotal > 20 ? (
          <nav className="pagination" aria-label={tc('page', { page: ownedPage })}>
            <button
              className="button secondary"
              type="button"
              disabled={ownedPage <= 1}
              onClick={() => {
                setOwnedState('loading');
                setOwnedPage((page) => Math.max(1, page - 1));
              }}
            >
              {tc('previous')}
            </button>
            <span>{tc('page', { page: ownedPage })}</span>
            <button
              className="button secondary"
              type="button"
              disabled={ownedPage * 20 >= ownedTotal}
              onClick={() => {
                setOwnedState('loading');
                setOwnedPage((page) => page + 1);
              }}
            >
              {tc('next')}
            </button>
          </nav>
        ) : null}
      </AsyncState>
      {ownedState === 'error' ? (
        <button
          className="button secondary"
          type="button"
          onClick={() => {
            setOwnedState('loading');
            void loadOwnedChallenges();
          }}
        >
          {tc('tryAgain')}
        </button>
      ) : null}
    </section>
  );

  if (created)
    return (
      <div className="content-stack">
        <section className="panel share-panel">
          <h2>{t('createdTitle')}</h2>
          <p>{t('createdBody')}</p>
          <label>
            {tc('shareable')}
            <input
              name="share-url"
              autoComplete="off"
              spellCheck={false}
              readOnly
              value={shareUrl}
            />
          </label>
          <div className="button-row">
            <button className="button primary" type="button" onClick={() => void copy()}>
              {copyState === 'copied' ? tc('copied') : tc('copy')}
            </button>
            {created.id && !created.revoked ? (
              <button className="button danger" type="button" onClick={() => void revoke()}>
                {t('revoke')}
              </button>
            ) : null}
          </div>
          <p
            className="sr-only"
            role={copyState === 'error' ? 'alert' : 'status'}
            aria-live="polite"
          >
            {copyState === 'copied' ? tc('copied') : copyState === 'error' ? tc('copyError') : ''}
          </p>
          {results ? (
            <section className="challenge-results" aria-labelledby="challenge-results-heading">
              <h3 id="challenge-results-heading">{t('resultsTitle')}</h3>
              <ChallengeResultBoard
                results={results}
                onPageChange={(page) => {
                  setResults(null);
                  setResultsError(false);
                  setResultsPage(page);
                }}
              />
            </section>
          ) : resultsError ? (
            <p className="quiet-note">{t('resultsError')}</p>
          ) : (
            <p className="quiet-note" role="status">
              {t('loadingResults')}
            </p>
          )}
          {error ? (
            <p className="inline-error" role="alert">
              {error}
            </p>
          ) : null}
        </section>
        {managementPanel}
      </div>
    );

  return (
    <div className="content-stack">
      <form className="setup-form" onSubmit={(event) => void create(event)}>
        <label>
          {t('titleLabel')} <span className="quiet-note">({tc('optional')})</span>
          <input
            name="challenge-title"
            autoComplete="off"
            maxLength={80}
            value={title}
            onChange={(event) => {
              setTitle(event.target.value);
              creationKeyRef.current = null;
            }}
            aria-describedby="challenge-title-hint"
          />
          <small id="challenge-title-hint">{t('titleHint')}</small>
        </label>
        <fieldset className="choice-group">
          <legend>{tp('difficulty')}</legend>
          <div className="segmented-options">
            {(['easy', 'normal', 'hard', 'expert', 'custom'] as const).map((value) => (
              <label key={value}>
                <input
                  type="radio"
                  name="challenge-difficulty"
                  checked={difficulty === value}
                  onChange={() => {
                    setDifficulty(value);
                    setSecret([]);
                    creationKeyRef.current = null;
                  }}
                />
                <span>{tp(value)}</span>
              </label>
            ))}
          </div>
        </fieldset>
        {difficulty === 'custom' ? (
          <div className="form-grid panel">
            <label>
              {tp('colours')}
              <input
                type="number"
                name="challenge-colour-count"
                inputMode="numeric"
                min="5"
                max="10"
                value={colourCount}
                onChange={(event) => {
                  setColourCount(Number(event.target.value));
                  setSecret([]);
                  creationKeyRef.current = null;
                }}
              />
            </label>
            <label>
              {tp('codeLength')}
              <input
                type="number"
                name="challenge-code-length"
                inputMode="numeric"
                min="3"
                max="6"
                value={codeLength}
                onChange={(event) => {
                  setCodeLength(Number(event.target.value));
                  setSecret([]);
                  creationKeyRef.current = null;
                }}
              />
            </label>
            <label>
              {tp('maximumAttempts')}
              <input
                type="number"
                name="challenge-max-attempts"
                inputMode="numeric"
                min="1"
                max="20"
                value={maxAttempts}
                onChange={(event) => {
                  setMaxAttempts(Number(event.target.value));
                  creationKeyRef.current = null;
                }}
              />
            </label>
            <label className="check-row">
              <input
                type="checkbox"
                name="challenge-duplicates"
                checked={duplicatesAllowed}
                onChange={(event) => {
                  setDuplicatesAllowed(event.target.checked);
                  setSecret([]);
                  creationKeyRef.current = null;
                }}
              />
              <span>{tp('duplicates')}</span>
            </label>
            {invalidCustom ? (
              <p className="inline-error" role="alert">
                {tp('invalidCustom')}
              </p>
            ) : null}
          </div>
        ) : null}
        <fieldset className="choice-group">
          <legend>{t('secretMethod')}</legend>
          <div className="segmented-options">
            <label>
              <input
                type="radio"
                name="secret-method"
                checked={!manual}
                onChange={() => {
                  setManual(false);
                  setSecret([]);
                  creationKeyRef.current = null;
                }}
              />
              <span>{t('generated')}</span>
            </label>
            <label>
              <input
                type="radio"
                name="secret-method"
                checked={manual}
                onChange={() => {
                  setManual(true);
                  setSecret([]);
                  creationKeyRef.current = null;
                }}
              />
              <span>{t('manual')}</span>
            </label>
          </div>
        </fieldset>
        {manual ? (
          <fieldset className="secret-picker panel">
            <legend>{tp('secret')}</legend>
            <div className="secret-row" role="group" aria-label={tp('secret')}>
              {Array.from({ length: selectedRules.length }, (_, index) => {
                const colour = secret[index];
                return (
                  <span
                    key={index}
                    className={`peg slot ${colour ? `peg-${colour}` : ''}`}
                    role="img"
                    aria-label={colour ? tg(`colors.${colour}`) : tg('empty')}
                  >
                    {colour ? symbols[colour] : index + 1}
                  </span>
                );
              })}
            </div>
            <div className="palette">
              {selectedRules.colours.map((colour) => (
                <button
                  key={colour}
                  className={`peg peg-${colour}`}
                  type="button"
                  aria-label={tg(`colors.${colour}`)}
                  onClick={() => {
                    setSecret((current) =>
                      !selectedRules.duplicates && current.includes(colour)
                        ? current
                        : [...current, colour].slice(0, selectedRules.length),
                    );
                    creationKeyRef.current = null;
                  }}
                >
                  {symbols[colour]}
                </button>
              ))}
            </div>
            <button
              className="text-button"
              type="button"
              disabled={secret.length === 0}
              onClick={() => {
                setSecret((current) => current.slice(0, -1));
                creationKeyRef.current = null;
              }}
            >
              {tg('clear')}
            </button>
            <small>{tg('serverAuthoritative')}</small>
          </fieldset>
        ) : null}
        <label className="check-row">
          <input
            type="checkbox"
            name="show-creator-name"
            checked={showCreatorName}
            onChange={(event) => {
              setShowCreatorName(event.target.checked);
              creationKeyRef.current = null;
            }}
          />
          <span>{t('creatorVisible')}</span>
        </label>
        {error ? (
          <p className="inline-error" role="alert">
            {error}
          </p>
        ) : null}
        <button
          className="button primary"
          type="submit"
          disabled={
            submitting || invalidCustom || (manual && secret.length !== selectedRules.length)
          }
        >
          {submitting ? t('creating') : t('create')}
        </button>
      </form>
      {managementPanel}
    </div>
  );
}

export function ChallengePlayer({ shareCode }: { shareCode: string }) {
  const locale = useLocale();
  const t = useTranslations('Challenges');
  const tc = useTranslations('Common');
  const api = useApi();
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');

  useEffect(() => {
    let active = true;
    api<Challenge>(`/v1/challenges/${encodeURIComponent(shareCode)}`)
      .then((value) => {
        if (active) {
          setChallenge(value);
          setState('ready');
        }
      })
      .catch(() => {
        if (active) setState('error');
      });
    return () => {
      active = false;
    };
  }, [api, shareCode]);

  return (
    <AsyncState
      state={state}
      loadingLabel={tc('loading')}
      errorLabel={t('loadError')}
      emptyLabel={t('expired')}
    >
      {challenge && !challenge.revoked ? (
        <div className="challenge-layout">
          <section className="panel">
            <p className="mode-label">{t('playTitle')}</p>
            {challenge.title ? <h2>{challenge.title}</h2> : null}
            {challenge.creatorName ? (
              <p>
                {t('from', {
                  name:
                    challenge.creatorName === 'Anonymous breaker'
                      ? tc('anonymous')
                      : challenge.creatorName,
                })}
              </p>
            ) : null}
            {challenge.id ? (
              <p>{t('completedCount', { count: challenge.completedCount })}</p>
            ) : null}
            <h3>{t('rules')}</h3>
            <dl className="rules-summary">
              <div>
                <dt>{challenge.config.colours.length}</dt>
                <dd>× {challenge.config.codeLength}</dd>
              </div>
              <div>
                <dt>{challenge.config.maxAttempts}</dt>
                <dd>{tc('attempts', { count: challenge.config.maxAttempts })}</dd>
              </div>
            </dl>
            <p className="quiet-note">
              {new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(
                new Date(challenge.expiresAt),
              )}
            </p>
          </section>
          <GameBoard
            title={challenge.title ?? t('playTitle')}
            startEndpoint={`/v1/challenges/${encodeURIComponent(shareCode)}/start`}
            startBody={{ practice: false }}
            replayBody={{ practice: true }}
            replayLabel={t('replay')}
          />
        </div>
      ) : null}
    </AsyncState>
  );
}
