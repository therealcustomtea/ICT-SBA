// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useLocale, useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useEffect, useRef, useState } from 'react';
// Imports the dependency used by this module.
import { AsyncState } from '@/components/feature-page';
// Imports the dependency used by this module.
import { GameBoard } from '@/components/game-board';
// Imports the dependency used by this module.
import { type Challenge, type ChallengeResults, useApi } from '@/lib/api';
// Imports the dependency used by this module.
import { useProductAnalytics } from '@/lib/use-product-analytics';

// Computes and stores colourIds for subsequent operations.
const colourIds = ['R', 'B', 'G', 'Y', 'W', 'K', 'O', 'P', 'C', 'M'] as const;
// Computes and stores challengePresets for subsequent operations.
const challengePresets = {
  // Defines the easy field in the surrounding object or type.
  easy: { colours: colourIds.slice(0, 5), length: 4, maxAttempts: 12, duplicates: false },
  // Defines the normal field in the surrounding object or type.
  normal: { colours: colourIds.slice(0, 6), length: 4, maxAttempts: 10, duplicates: true },
  // Defines the hard field in the surrounding object or type.
  hard: { colours: colourIds.slice(0, 8), length: 5, maxAttempts: 8, duplicates: true },
  // Defines the expert field in the surrounding object or type.
  expert: { colours: colourIds.slice(0, 10), length: 6, maxAttempts: 8, duplicates: true },
  // Executes this line as the next step in the surrounding logic.
} as const;
// Computes and stores symbols for subsequent operations.
const symbols: Record<string, string> = {
  // Defines the R field in the surrounding object or type.
  R: '●',
  // Defines the B field in the surrounding object or type.
  B: '◆',
  // Defines the G field in the surrounding object or type.
  G: '▲',
  // Defines the Y field in the surrounding object or type.
  Y: '■',
  // Defines the W field in the surrounding object or type.
  W: '○',
  // Defines the K field in the surrounding object or type.
  K: '✚',
  // Defines the O field in the surrounding object or type.
  O: '⬟',
  // Defines the P field in the surrounding object or type.
  P: '✦',
  // Defines the C field in the surrounding object or type.
  C: '⬢',
  // Defines the M field in the surrounding object or type.
  M: '♥',
  // Closes the expression, call, or declaration started above.
};
// Declares the OwnedChallenge data shape or implementation.
type OwnedChallenge = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Defines the title field in the surrounding object or type.
  title: string | null;
  // Defines the showCreatorName field in the surrounding object or type.
  showCreatorName: boolean;
  // Defines the config field in the surrounding object or type.
  config: Challenge['config'];
  // Defines the revoked field in the surrounding object or type.
  revoked: boolean;
  // Defines the expiresAt field in the surrounding object or type.
  expiresAt: string;
  // Defines the completedCount field in the surrounding object or type.
  completedCount: number;
  // Defines the createdAt field in the surrounding object or type.
  createdAt: string;
  // Closes the expression, call, or declaration started above.
};
// Declares the OwnedChallengesResponse data shape or implementation.
type OwnedChallengesResponse = {
  // Defines the items field in the surrounding object or type.
  items: OwnedChallenge[];
  // Defines the page field in the surrounding object or type.
  page: number;
  // Defines the pageSize field in the surrounding object or type.
  pageSize: number;
  // Defines the total field in the surrounding object or type.
  total: number;
  // Closes the expression, call, or declaration started above.
};
// Computes and stores RESULTS_PAGE_SIZE for subsequent operations.
const RESULTS_PAGE_SIZE = 10;

// Defines the ChallengeResultBoard function and its callable behavior.
function ChallengeResultBoard({
  // Supplies this item to the surrounding call or collection.
  results,
  // Provides the compact value to the surrounding call or element.
  compact = false,
  // Supplies this item to the surrounding call or collection.
  onPageChange,
  // Begins the nested block or object completed below.
}: {
  // Defines the results field in the surrounding object or type.
  results: ChallengeResults;
  // Executes this line as the next step in the surrounding logic.
  compact?: boolean;
  // Executes this line as the next step in the surrounding logic.
  onPageChange?: (page: number) => void;
  // Begins the nested block or object completed below.
}) {
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Challenges');
  // Computes and stores tg for subsequent operations.
  const tg = useTranslations('Game');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores numberFormat for subsequent operations.
  const numberFormat = new Intl.NumberFormat(locale);
  // Computes and stores completedAtFormat for subsequent operations.
  const completedAtFormat = new Intl.DateTimeFormat(locale, {
    // Defines the dateStyle field in the surrounding object or type.
    dateStyle: 'medium',
    // Defines the timeStyle field in the surrounding object or type.
    timeStyle: 'short',
    // Closes the expression, call, or declaration started above.
  });

  // Returns this result to the caller and ends the current function.
  return (
    // Starts a JSX fragment that groups the following interface elements.
    <>
      {/* Renders the dl interface element or component. */}
      <dl className={`rules-summary${compact ? ' compact-results' : ''}`}>
        {/* Renders the div interface element or component. */}
        <div>
          {/* Renders the dt interface element or component. */}
          <dt>{t('completed')}</dt>
          {/* Renders the dd interface element or component. */}
          <dd>{results.completedCount}</dd>
          {/* Closes the div interface element. */}
        </div>
        {/* Renders the div interface element or component. */}
        <div>
          {/* Renders the dt interface element or component. */}
          <dt>{t('winRate')}</dt>
          {/* Renders the dd interface element or component. */}
          <dd>{results.winRate}%</dd>
          {/* Closes the div interface element. */}
        </div>
        {/* Renders the div interface element or component. */}
        <div>
          {/* Renders the dt interface element or component. */}
          <dt>{t('averageAttempts')}</dt>
          {/* Renders the dd interface element or component. */}
          <dd>{results.averageAttempts ?? '—'}</dd>
          {/* Closes the div interface element. */}
        </div>
        {/* Closes the dl interface element. */}
      </dl>
      {/* Executes this line as the next step in the surrounding logic. */}
      {results.items.length ? (
        // Starts a JSX fragment that groups the following interface elements.
        <>
          {/* Renders the p interface element or component. */}
          <p className="quiet-note">{t('resultsOrder')}</p>
          {/* Renders the div interface element or component. */}
          <div
            /* Provides the className value to the surrounding call or element. */
            className="table-scroll challenge-results-table"
            /* Provides the role value to the surrounding call or element. */
            role="region"
            /* Executes this line as the next step in the surrounding logic. */
            aria-label={t('resultsTableRegion')}
            /* Provides the tabIndex value to the surrounding call or element. */
            tabIndex={0}
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Renders the table interface element or component. */}
            <table>
              {/* Renders the caption interface element or component. */}
              <caption className="sr-only">{t('resultsTitle')}</caption>
              {/* Renders the thead interface element or component. */}
              <thead>
                {/* Renders the tr interface element or component. */}
                <tr>
                  {/* Renders the th interface element or component. */}
                  <th scope="col">{t('rank')}</th>
                  {/* Renders the th interface element or component. */}
                  <th scope="col">{t('player')}</th>
                  {/* Renders the th interface element or component. */}
                  <th scope="col">{t('result')}</th>
                  {/* Renders the th interface element or component. */}
                  <th scope="col">{t('score')}</th>
                  {/* Renders the th interface element or component. */}
                  <th scope="col">{t('attempts')}</th>
                  {/* Renders the th interface element or component. */}
                  <th scope="col">{t('time')}</th>
                  {/* Renders the th interface element or component. */}
                  <th scope="col">{t('completedAt')}</th>
                  {/* Closes the tr interface element. */}
                </tr>
                {/* Closes the thead interface element. */}
              </thead>
              {/* Renders the tbody interface element or component. */}
              <tbody>
                {/* Begins the nested block or object completed below. */}
                {results.items.map((item) => {
                  // Computes and stores playerToken for subsequent operations.
                  const playerToken = item.playerLabel.startsWith('Breaker ')
                    ? // Continues the surrounding operation with this required value or expression.
                      // Executes this line as the next step in the surrounding logic.
                      item.playerLabel.slice('Breaker '.length)
                    : // Continues the surrounding operation with this required value or expression.
                      // Executes this line as the next step in the surrounding logic.
                      item.playerLabel;
                  // Computes and stores knownResult for subsequent operations.
                  const knownResult = [
                    // Supplies this item to the surrounding call or collection.
                    'created',
                    // Supplies this item to the surrounding call or collection.
                    'active',
                    // Supplies this item to the surrounding call or collection.
                    'won',
                    // Supplies this item to the surrounding call or collection.
                    'lost',
                    // Supplies this item to the surrounding call or collection.
                    'abandoned',
                    // Supplies this item to the surrounding call or collection.
                    'expired',
                    // Executes this line as the next step in the surrounding logic.
                  ].includes(item.result)
                    ? // Continues the surrounding operation with this required value or expression.
                      // Executes this line as the next step in the surrounding logic.
                      item.result
                    : // Continues the surrounding operation with this required value or expression.
                      // Executes this line as the next step in the surrounding logic.
                      null;
                  // Returns this result to the caller and ends the current function.
                  return (
                    // Renders the tr interface element or component.
                    <tr key={`${item.rank}-${item.playerLabel}`}>
                      {/* Renders the td interface element or component. */}
                      <td>{item.rank}</td>
                      {/* Renders the th interface element or component. */}
                      <th scope="row">{t('breakerLabel', { token: playerToken })}</th>
                      {/* Renders the td interface element or component. */}
                      <td>
                        {/* Renders the span interface element or component. */}
                        <span className={`status ${knownResult ?? 'muted'}`}>
                          {/* Executes this line as the next step in the surrounding logic. */}
                          {knownResult ? tg(`status.${knownResult}`) : tc('unavailable')}
                          {/* Closes the span interface element. */}
                        </span>
                        {/* Closes the td interface element. */}
                      </td>
                      {/* Renders the td interface element or component. */}
                      <td>{numberFormat.format(item.score)}</td>
                      {/* Renders the td interface element or component. */}
                      <td>
                        {/* Begins the nested block or object completed below. */}
                        {t('attemptsOf', {
                          // Defines the used field in the surrounding object or type.
                          used: item.attemptsUsed,
                          // Defines the maximum field in the surrounding object or type.
                          maximum: item.maxAttempts,
                          // Closes the expression, call, or declaration started above.
                        })}
                        {/* Closes the td interface element. */}
                      </td>
                      {/* Renders the td interface element or component. */}
                      <td>
                        {/* Executes this line as the next step in the surrounding logic. */}
                        {item.elapsedSeconds === null
                          ? // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            tc('unavailable')
                          : // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            formatChallengeDuration(item.elapsedSeconds)}
                        {/* Closes the td interface element. */}
                      </td>
                      {/* Renders the td interface element or component. */}
                      <td>
                        {/* Renders the time interface element or component. */}
                        <time dateTime={item.completedAt}>
                          {/* Executes this line as the next step in the surrounding logic. */}
                          {completedAtFormat.format(new Date(item.completedAt))}
                          {/* Closes the time interface element. */}
                        </time>
                        {/* Closes the td interface element. */}
                      </td>
                      {/* Closes the tr interface element. */}
                    </tr>
                    // Closes the expression, call, or declaration started above.
                  );
                  // Closes the expression, call, or declaration started above.
                })}
                {/* Closes the tbody interface element. */}
              </tbody>
              {/* Closes the table interface element. */}
            </table>
            {/* Closes the div interface element. */}
          </div>
          {/* Executes this line as the next step in the surrounding logic. */}
          {onPageChange && results.total > results.pageSize ? (
            // Renders the nav interface element or component.
            <nav className="pagination" aria-label={t('resultsPage', { page: results.page })}>
              {/* Renders the button interface element or component. */}
              <button
                /* Provides the className value to the surrounding call or element. */
                className="button secondary"
                /* Provides the type value to the surrounding call or element. */
                type="button"
                /* Provides the disabled value to the surrounding call or element. */
                disabled={results.page <= 1}
                /* Provides the onClick value to the surrounding call or element. */
                onClick={() => onPageChange(Math.max(1, results.page - 1))}
                /* Closes the expression, call, or declaration started above. */
              >
                {/* Executes this line as the next step in the surrounding logic. */}
                {tc('previous')}
                {/* Closes the button interface element. */}
              </button>
              {/* Renders the span interface element or component. */}
              <span>{tc('page', { page: results.page })}</span>
              {/* Renders the button interface element or component. */}
              <button
                /* Provides the className value to the surrounding call or element. */
                className="button secondary"
                /* Provides the type value to the surrounding call or element. */
                type="button"
                /* Provides the disabled value to the surrounding call or element. */
                disabled={results.page * results.pageSize >= results.total}
                /* Provides the onClick value to the surrounding call or element. */
                onClick={() => onPageChange(results.page + 1)}
                /* Closes the expression, call, or declaration started above. */
              >
                {/* Executes this line as the next step in the surrounding logic. */}
                {tc('next')}
                {/* Closes the button interface element. */}
              </button>
              {/* Closes the nav interface element. */}
            </nav>
          ) : // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          null}
          {/* Closes the JSX fragment started above. */}
        </>
      ) : (
        // Executes this line as the next step in the surrounding logic.
        // Renders the p interface element or component.
        <p className="quiet-note">{t('resultsEmpty')}</p>
        // Closes the expression, call, or declaration started above.
      )}
      {/* Closes the JSX fragment started above. */}
    </>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Defines the formatChallengeDuration function and its callable behavior.
function formatChallengeDuration(seconds: number) {
  // Returns this result to the caller and ends the current function.
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function ChallengeCreator() {
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Challenges');
  // Computes and stores tp for subsequent operations.
  const tp = useTranslations('Play');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores tg for subsequent operations.
  const tg = useTranslations('Game');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Computes and stores analytics for subsequent operations.
  const analytics = useProductAnalytics();
  // Executes this line as the next step in the surrounding logic.
  const [difficulty, setDifficulty] = useState<'easy' | 'normal' | 'hard' | 'expert' | 'custom'>(
    // Supplies this item to the surrounding call or collection.
    'normal',
    // Closes the expression, call, or declaration started above.
  );
  // Executes this line as the next step in the surrounding logic.
  const [colourCount, setColourCount] = useState(6);
  // Executes this line as the next step in the surrounding logic.
  const [codeLength, setCodeLength] = useState(4);
  // Executes this line as the next step in the surrounding logic.
  const [maxAttempts, setMaxAttempts] = useState(10);
  // Executes this line as the next step in the surrounding logic.
  const [duplicatesAllowed, setDuplicatesAllowed] = useState(true);
  // Executes this line as the next step in the surrounding logic.
  const [title, setTitle] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [showCreatorName, setShowCreatorName] = useState(true);
  // Executes this line as the next step in the surrounding logic.
  const [manual, setManual] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [secret, setSecret] = useState<string[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [created, setCreated] = useState<Challenge | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [submitting, setSubmitting] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');
  // Executes this line as the next step in the surrounding logic.
  const [results, setResults] = useState<ChallengeResults | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [resultsError, setResultsError] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [resultsPage, setResultsPage] = useState(1);
  // Executes this line as the next step in the surrounding logic.
  const [ownedChallenges, setOwnedChallenges] = useState<OwnedChallenge[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [ownedState, setOwnedState] = useState<'loading' | 'error' | 'empty' | 'ready'>('loading');
  // Executes this line as the next step in the surrounding logic.
  const [ownedPage, setOwnedPage] = useState(1);
  // Executes this line as the next step in the surrounding logic.
  const [ownedTotal, setOwnedTotal] = useState(0);
  // Begins the nested block or object completed below.
  const [ownedResults, setOwnedResults] = useState<{
    // Defines the challengeId field in the surrounding object or type.
    challengeId: string;
    // Defines the state field in the surrounding object or type.
    state: 'loading' | 'error' | 'ready';
    // Defines the data field in the surrounding object or type.
    data: ChallengeResults | null;
    // Executes this line as the next step in the surrounding logic.
  } | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [revokingId, setRevokingId] = useState<string | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [ownedActionErrorId, setOwnedActionErrorId] = useState<string | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [renderedAt] = useState(Date.now);
  // Computes and stores creationKeyRef for subsequent operations.
  const creationKeyRef = useRef<string | null>(null);
  // Computes and stores selectedRules for subsequent operations.
  const selectedRules =
    // Provides the difficulty value to the surrounding call or element.
    difficulty === 'custom'
      ? // Continues the surrounding operation with this required value or expression.
        // Begins the nested block or object completed below.
        {
          // Defines the colours field in the surrounding object or type.
          colours: colourIds.slice(0, colourCount),
          // Defines the length field in the surrounding object or type.
          length: codeLength,
          // Supplies this item to the surrounding call or collection.
          maxAttempts,
          // Defines the duplicates field in the surrounding object or type.
          duplicates: duplicatesAllowed,
          // Closes the expression, call, or declaration started above.
        }
      : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        challengePresets[difficulty];
  // Computes and stores invalidCustom for subsequent operations.
  const invalidCustom = difficulty === 'custom' && !duplicatesAllowed && colourCount < codeLength;

  // Computes and stores loadOwnedChallenges for subsequent operations.
  const loadOwnedChallenges = async () => {
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores response for subsequent operations.
      const response = await api<OwnedChallengesResponse>(
        // Supplies this item to the surrounding call or collection.
        `/v1/challenges/mine?page=${ownedPage}&page_size=20`,
        // Closes the expression, call, or declaration started above.
      );
      // Calls setOwnedChallenges with the supplied values.
      setOwnedChallenges(response.items);
      // Calls setOwnedTotal with the supplied values.
      setOwnedTotal(response.total);
      // Calls setOwnedState with the supplied values.
      setOwnedState(response.items.length ? 'ready' : 'empty');
      // Handles a failure from the protected operation.
    } catch {
      // Calls setOwnedState with the supplied values.
      setOwnedState('error');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Executes this line as the next step in the surrounding logic.
    api<OwnedChallengesResponse>(`/v1/challenges/mine?page=${ownedPage}&page_size=20`)
      // Begins the nested block or object completed below.
      .then((response) => {
        // Checks this condition before running the nested branch.
        if (active) {
          // Calls setOwnedChallenges with the supplied values.
          setOwnedChallenges(response.items);
          // Calls setOwnedTotal with the supplied values.
          setOwnedTotal(response.total);
          // Calls setOwnedState with the supplied values.
          setOwnedState(response.items.length ? 'ready' : 'empty');
          // Closes the expression, call, or declaration started above.
        }
        // Closes the expression, call, or declaration started above.
      })
      // Begins the nested block or object completed below.
      .catch(() => {
        // Checks this condition before running the nested branch.
        if (active) setOwnedState('error');
        // Closes the expression, call, or declaration started above.
      });
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api, ownedPage]);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Checks this condition before running the nested branch.
    if (!created?.id) return;
    // Computes and stores active for subsequent operations.
    let active = true;
    // Executes this line as the next step in the surrounding logic.
    api<ChallengeResults>(
      // Supplies this item to the surrounding call or collection.
      `/v1/challenges/${encodeURIComponent(created.id)}/results?page=${resultsPage}&page_size=${RESULTS_PAGE_SIZE}`,
      // Closes the expression, call, or declaration started above.
    )
      // Begins the nested block or object completed below.
      .then((value) => {
        // Checks this condition before running the nested branch.
        if (active) setResults(value);
        // Closes the expression, call, or declaration started above.
      })
      // Begins the nested block or object completed below.
      .catch(() => {
        // Checks this condition before running the nested branch.
        if (active) setResultsError(true);
        // Closes the expression, call, or declaration started above.
      });
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api, created?.id, resultsPage]);

  // Computes and stores create for subsequent operations.
  const create = async (event: React.FormEvent<HTMLFormElement>) => {
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Checks this condition before running the nested branch.
    if (invalidCustom || (manual && secret.length !== selectedRules.length)) return;
    // Calls setSubmitting with the supplied values.
    setSubmitting(true);
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Executes this line as the next step in the surrounding logic.
      creationKeyRef.current ??= crypto.randomUUID();
      // Computes and stores selection for subsequent operations.
      const selection =
        // Provides the difficulty value to the surrounding call or element.
        difficulty === 'custom'
          ? // Continues the surrounding operation with this required value or expression.
            // Begins the nested block or object completed below.
            {
              // Defines the config field in the surrounding object or type.
              config: {
                // Defines the colours field in the surrounding object or type.
                colours: [...selectedRules.colours],
                // Defines the codeLength field in the surrounding object or type.
                codeLength: selectedRules.length,
                // Defines the maxAttempts field in the surrounding object or type.
                maxAttempts: selectedRules.maxAttempts,
                // Defines the duplicatesAllowed field in the surrounding object or type.
                duplicatesAllowed: selectedRules.duplicates,
                // Defines the codeMaker field in the surrounding object or type.
                codeMaker: manual ? 'human' : 'computer',
                // Defines the visibility field in the surrounding object or type.
                visibility: 'shareable',
                // Defines the ranked field in the surrounding object or type.
                ranked: false,
                // Defines the timeBonusCap field in the surrounding object or type.
                timeBonusCap: 300,
                // Closes the expression, call, or declaration started above.
              },
              // Closes the expression, call, or declaration started above.
            }
          : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            { difficulty };
      // Computes and stores challenge for subsequent operations.
      const challenge = await api<Challenge>('/v1/challenges', {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Defines the body field in the surrounding object or type.
        body: JSON.stringify({
          // Supplies this item to the surrounding call or collection.
          ...selection,
          // Defines the title field in the surrounding object or type.
          title: title || null,
          // Supplies this item to the surrounding call or collection.
          showCreatorName,
          // Defines the idempotencyKey field in the surrounding object or type.
          idempotencyKey: creationKeyRef.current,
          // Supplies this item to the surrounding call or collection.
          ...(manual ? { secret } : {}),
          // Closes the expression, call, or declaration started above.
        }),
        // Closes the expression, call, or declaration started above.
      });
      // Calls setSecret with the supplied values.
      setSecret([]);
      // Calls setResults with the supplied values.
      setResults(null);
      // Calls setResultsError with the supplied values.
      setResultsError(false);
      // Calls setResultsPage with the supplied values.
      setResultsPage(1);
      // Calls setCreated with the supplied values.
      setCreated(challenge);
      // Executes this line as the next step in the surrounding logic.
      creationKeyRef.current = null;
      // Calls analytics with the supplied values.
      analytics('friend_challenge_created', { official: true, expiryBand: '30_days' });
      // Checks this condition before running the nested branch.
      if (ownedPage === 1) void loadOwnedChallenges();
      // Handles the remaining unmatched case.
      else {
        // Calls setOwnedState with the supplied values.
        setOwnedState('loading');
        // Calls setOwnedPage with the supplied values.
        setOwnedPage(1);
        // Closes the expression, call, or declaration started above.
      }
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('createError'));
      // Runs cleanup regardless of the protected result.
    } finally {
      // Calls setSubmitting with the supplied values.
      setSubmitting(false);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores shareUrl for subsequent operations.
  const shareUrl =
    // Executes this line as the next step in the surrounding logic.
    created && typeof window !== 'undefined'
      ? // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        `${window.location.origin}${window.location.pathname.replace('/new', `/${created.shareCode}`)}`
      : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        '';
  // Computes and stores copy for subsequent operations.
  const copy = async () => {
    // Checks this condition before running the nested branch.
    if (!shareUrl) return;
    // Starts an operation whose expected failures are handled below.
    try {
      // Waits for this asynchronous operation to complete.
      await navigator.clipboard.writeText(shareUrl);
      // Calls setCopyState with the supplied values.
      setCopyState('copied');
      // Handles a failure from the protected operation.
    } catch {
      // Calls setCopyState with the supplied values.
      setCopyState('error');
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };
  // Computes and stores revoke for subsequent operations.
  const revoke = async () => {
    // Checks this condition before running the nested branch.
    if (!created?.id || !confirm(t('revokeConfirm'))) return;
    // Starts an operation whose expected failures are handled below.
    try {
      // Waits for this asynchronous operation to complete.
      await api<void>(`/v1/challenges/${encodeURIComponent(created.id)}`, { method: 'DELETE' });
      // Calls setCreated with the supplied values.
      setCreated({ ...created, revoked: true });
      // Calls setOwnedChallenges with the supplied values.
      setOwnedChallenges(
        // Continues the surrounding operation with this required value or expression.
        (current) =>
          // Calls current.map with the supplied values.
          current.map((item) => (item.id === created.id ? { ...item, revoked: true } : item)),
        // Closes the expression, call, or declaration started above.
      );
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('createError'));
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores viewOwnedResults for subsequent operations.
  const viewOwnedResults = async (challengeId: string, page = 1) => {
    // Calls setOwnedResults with the supplied values.
    setOwnedResults({ challengeId, state: 'loading', data: null });
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores data for subsequent operations.
      const data = await api<ChallengeResults>(
        // Supplies this item to the surrounding call or collection.
        `/v1/challenges/${encodeURIComponent(challengeId)}/results?page=${page}&page_size=${RESULTS_PAGE_SIZE}`,
        // Closes the expression, call, or declaration started above.
      );
      // Calls setOwnedResults with the supplied values.
      setOwnedResults({ challengeId, state: 'ready', data });
      // Handles a failure from the protected operation.
    } catch {
      // Calls setOwnedResults with the supplied values.
      setOwnedResults({ challengeId, state: 'error', data: null });
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores revokeOwned for subsequent operations.
  const revokeOwned = async (challengeId: string) => {
    // Checks this condition before running the nested branch.
    if (!confirm(t('revokeConfirm'))) return;
    // Calls setRevokingId with the supplied values.
    setRevokingId(challengeId);
    // Calls setOwnedActionErrorId with the supplied values.
    setOwnedActionErrorId(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Waits for this asynchronous operation to complete.
      await api<void>(`/v1/challenges/${encodeURIComponent(challengeId)}`, { method: 'DELETE' });
      // Calls setOwnedChallenges with the supplied values.
      setOwnedChallenges(
        // Continues the surrounding operation with this required value or expression.
        (current) =>
          // Calls current.map with the supplied values.
          current.map((item) => (item.id === challengeId ? { ...item, revoked: true } : item)),
        // Closes the expression, call, or declaration started above.
      );
      // Checks this condition before running the nested branch.
      if (created?.id === challengeId) setCreated({ ...created, revoked: true });
      // Handles a failure from the protected operation.
    } catch {
      // Calls setOwnedActionErrorId with the supplied values.
      setOwnedActionErrorId(challengeId);
      // Runs cleanup regardless of the protected result.
    } finally {
      // Calls setRevokingId with the supplied values.
      setRevokingId(null);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Computes and stores managementPanel for subsequent operations.
  const managementPanel = (
    // Renders the section interface element or component.
    <section className="panel challenge-management" aria-labelledby="my-challenges-heading">
      {/* Renders the div interface element or component. */}
      <div>
        {/* Renders the h2 interface element or component. */}
        <h2 id="my-challenges-heading">{t('mineTitle')}</h2>
        {/* Renders the p interface element or component. */}
        <p className="quiet-note">{t('mineIntro')}</p>
        {/* Closes the div interface element. */}
      </div>
      {/* Renders the AsyncState interface element or component. */}
      <AsyncState
        /* Provides the state value to the surrounding call or element. */
        state={ownedState}
        /* Provides the loadingLabel value to the surrounding call or element. */
        loadingLabel={t('loadingMine')}
        /* Provides the errorLabel value to the surrounding call or element. */
        errorLabel={t('mineError')}
        /* Provides the emptyLabel value to the surrounding call or element. */
        emptyLabel={t('mineEmpty')}
        /* Closes the expression, call, or declaration started above. */
      >
        {/* Renders the ul interface element or component. */}
        <ul className="challenge-management-list">
          {/* Begins the nested block or object completed below. */}
          {ownedChallenges.map((item) => {
            // Computes and stores expired for subsequent operations.
            const expired = new Date(item.expiresAt).getTime() <= renderedAt;
            // Computes and stores statusKey for subsequent operations.
            const statusKey = item.revoked
              ? // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                'statusRevoked'
              : // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                expired
                ? // Continues the surrounding operation with this required value or expression.
                  // Executes this line as the next step in the surrounding logic.
                  'statusExpired'
                : // Continues the surrounding operation with this required value or expression.
                  // Executes this line as the next step in the surrounding logic.
                  'statusActive';
            // Computes and stores result for subsequent operations.
            const result = ownedResults?.challengeId === item.id ? ownedResults : null;
            // Returns this result to the caller and ends the current function.
            return (
              // Renders the li interface element or component.
              <li key={item.id}>
                {/* Renders the div interface element or component. */}
                <div className="challenge-management-summary">
                  {/* Renders the div interface element or component. */}
                  <div>
                    {/* Renders the h3 interface element or component. */}
                    <h3>{item.title ?? t('untitled')}</h3>
                    {/* Renders the p interface element or component. */}
                    <p>
                      {/* Renders the span interface element or component. */}
                      <span className={`status ${item.revoked || expired ? 'muted' : 'success'}`}>
                        {/* Executes this line as the next step in the surrounding logic. */}
                        {t(statusKey)}
                        {/* Closes the span interface element. */}
                      </span>{' '}
                      {/* Executes this line as the next step in the surrounding logic. */}·{' '}
                      {t('completedCount', { count: item.completedCount })}
                      {/* Closes the p interface element. */}
                    </p>
                    {/* Renders the small interface element or component. */}
                    <small>
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {new Intl.DateTimeFormat(locale, { dateStyle: 'medium' }).format(
                        // Supplies this item to the surrounding call or collection.
                        new Date(item.createdAt),
                        // Closes the expression, call, or declaration started above.
                      )}
                      {/* Closes the small interface element. */}
                    </small>
                    {/* Closes the div interface element. */}
                  </div>
                  {/* Renders the div interface element or component. */}
                  <div className="button-row">
                    {/* Renders the button interface element or component. */}
                    <button
                      /* Provides the className value to the surrounding call or element. */
                      className="button secondary"
                      /* Provides the type value to the surrounding call or element. */
                      type="button"
                      /* Provides the onClick value to the surrounding call or element. */
                      onClick={() => void viewOwnedResults(item.id)}
                      /* Closes the expression, call, or declaration started above. */
                    >
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {t('viewResults')}
                      {/* Closes the button interface element. */}
                    </button>
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {!item.revoked && !expired ? (
                      // Renders the button interface element or component.
                      <button
                        /* Provides the className value to the surrounding call or element. */
                        className="button danger"
                        /* Provides the type value to the surrounding call or element. */
                        type="button"
                        /* Provides the disabled value to the surrounding call or element. */
                        disabled={revokingId === item.id}
                        /* Provides the onClick value to the surrounding call or element. */
                        onClick={() => void revokeOwned(item.id)}
                        /* Closes the expression, call, or declaration started above. */
                      >
                        {/* Executes this line as the next step in the surrounding logic. */}
                        {revokingId === item.id ? t('revoking') : t('revoke')}
                        {/* Closes the button interface element. */}
                      </button>
                    ) : // Continues the surrounding operation with this required value or expression.
                    // Executes this line as the next step in the surrounding logic.
                    null}
                    {/* Closes the div interface element. */}
                  </div>
                  {/* Closes the div interface element. */}
                </div>
                {/* Executes this line as the next step in the surrounding logic. */}
                {ownedActionErrorId === item.id ? (
                  // Renders the p interface element or component.
                  <p className="inline-error" role="alert">
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {t('revokeError')}
                    {/* Closes the p interface element. */}
                  </p>
                ) : // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                null}
                {/* Executes this line as the next step in the surrounding logic. */}
                {result?.state === 'loading' ? (
                  // Renders the p interface element or component.
                  <p role="status">{t('loadingResults')}</p>
                ) : // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                result?.state === 'error' ? (
                  // Renders the p interface element or component.
                  <p className="inline-error" role="alert">
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {t('resultsError')}
                    {/* Closes the p interface element. */}
                  </p>
                ) : // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                result?.data ? (
                  // Renders the section interface element or component.
                  <section aria-labelledby={`challenge-results-${item.id}`}>
                    {/* Renders the h4 interface element or component. */}
                    <h4 id={`challenge-results-${item.id}`}>{t('resultsTitle')}</h4>
                    {/* Renders the ChallengeResultBoard interface element or component. */}
                    <ChallengeResultBoard
                      /* Executes this line as the next step in the surrounding logic. */
                      compact
                      /* Provides the results value to the surrounding call or element. */
                      results={result.data}
                      /* Provides the onPageChange value to the surrounding call or element. */
                      onPageChange={(page) => void viewOwnedResults(item.id, page)}
                      /* Executes this line as the next step in the surrounding logic. */
                    />
                    {/* Closes the section interface element. */}
                  </section>
                ) : // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                null}
                {/* Closes the li interface element. */}
              </li>
              // Closes the expression, call, or declaration started above.
            );
            // Closes the expression, call, or declaration started above.
          })}
          {/* Closes the ul interface element. */}
        </ul>
        {/* Executes this line as the next step in the surrounding logic. */}
        {ownedTotal > 20 ? (
          // Renders the nav interface element or component.
          <nav className="pagination" aria-label={tc('page', { page: ownedPage })}>
            {/* Renders the button interface element or component. */}
            <button
              /* Provides the className value to the surrounding call or element. */
              className="button secondary"
              /* Provides the type value to the surrounding call or element. */
              type="button"
              /* Provides the disabled value to the surrounding call or element. */
              disabled={ownedPage <= 1}
              /* Provides the onClick value to the surrounding call or element. */
              onClick={() => {
                // Calls setOwnedState with the supplied values.
                setOwnedState('loading');
                // Calls setOwnedPage with the supplied values.
                setOwnedPage((page) => Math.max(1, page - 1));
                // Closes the expression, call, or declaration started above.
              }}
              /* Closes the expression, call, or declaration started above. */
            >
              {/* Executes this line as the next step in the surrounding logic. */}
              {tc('previous')}
              {/* Closes the button interface element. */}
            </button>
            {/* Renders the span interface element or component. */}
            <span>{tc('page', { page: ownedPage })}</span>
            {/* Renders the button interface element or component. */}
            <button
              /* Provides the className value to the surrounding call or element. */
              className="button secondary"
              /* Provides the type value to the surrounding call or element. */
              type="button"
              /* Provides the disabled value to the surrounding call or element. */
              disabled={ownedPage * 20 >= ownedTotal}
              /* Provides the onClick value to the surrounding call or element. */
              onClick={() => {
                // Calls setOwnedState with the supplied values.
                setOwnedState('loading');
                // Calls setOwnedPage with the supplied values.
                setOwnedPage((page) => page + 1);
                // Closes the expression, call, or declaration started above.
              }}
              /* Closes the expression, call, or declaration started above. */
            >
              {/* Executes this line as the next step in the surrounding logic. */}
              {tc('next')}
              {/* Closes the button interface element. */}
            </button>
            {/* Closes the nav interface element. */}
          </nav>
        ) : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        null}
        {/* Closes the AsyncState interface element. */}
      </AsyncState>
      {/* Executes this line as the next step in the surrounding logic. */}
      {ownedState === 'error' ? (
        // Renders the button interface element or component.
        <button
          /* Provides the className value to the surrounding call or element. */
          className="button secondary"
          /* Provides the type value to the surrounding call or element. */
          type="button"
          /* Provides the onClick value to the surrounding call or element. */
          onClick={() => {
            // Calls setOwnedState with the supplied values.
            setOwnedState('loading');
            // Executes this line as the next step in the surrounding logic.
            void loadOwnedChallenges();
            // Closes the expression, call, or declaration started above.
          }}
          /* Closes the expression, call, or declaration started above. */
        >
          {/* Executes this line as the next step in the surrounding logic. */}
          {tc('tryAgain')}
          {/* Closes the button interface element. */}
        </button>
      ) : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      null}
      {/* Closes the section interface element. */}
    </section>
    // Closes the expression, call, or declaration started above.
  );

  // Checks this condition before running the nested branch.
  if (created)
    // Returns this result to the caller and ends the current function.
    return (
      // Renders the div interface element or component.
      <div className="content-stack">
        {/* Renders the section interface element or component. */}
        <section className="panel share-panel">
          {/* Renders the h2 interface element or component. */}
          <h2>{t('createdTitle')}</h2>
          {/* Renders the p interface element or component. */}
          <p>{t('createdBody')}</p>
          {/* Renders the label interface element or component. */}
          <label>
            {/* Executes this line as the next step in the surrounding logic. */}
            {tc('shareable')}
            {/* Renders the input interface element or component. */}
            <input
              /* Provides the name value to the surrounding call or element. */
              name="share-url"
              /* Provides the autoComplete value to the surrounding call or element. */
              autoComplete="off"
              /* Provides the spellCheck value to the surrounding call or element. */
              spellCheck={false}
              /* Executes this line as the next step in the surrounding logic. */
              readOnly
              /* Provides the value value to the surrounding call or element. */
              value={shareUrl}
              /* Executes this line as the next step in the surrounding logic. */
            />
            {/* Closes the label interface element. */}
          </label>
          {/* Renders the div interface element or component. */}
          <div className="button-row">
            {/* Renders the button interface element or component. */}
            <button className="button primary" type="button" onClick={() => void copy()}>
              {/* Executes this line as the next step in the surrounding logic. */}
              {copyState === 'copied' ? tc('copied') : tc('copy')}
              {/* Closes the button interface element. */}
            </button>
            {/* Executes this line as the next step in the surrounding logic. */}
            {created.id && !created.revoked ? (
              // Renders the button interface element or component.
              <button className="button danger" type="button" onClick={() => void revoke()}>
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('revoke')}
                {/* Closes the button interface element. */}
              </button>
            ) : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            null}
            {/* Closes the div interface element. */}
          </div>
          {/* Renders the p interface element or component. */}
          <p
            /* Provides the className value to the surrounding call or element. */
            className="sr-only"
            /* Provides the role value to the surrounding call or element. */
            role={copyState === 'error' ? 'alert' : 'status'}
            /* Executes this line as the next step in the surrounding logic. */
            aria-live="polite"
            /* Closes the expression, call, or declaration started above. */
          >
            {/* Executes this line as the next step in the surrounding logic. */}
            {copyState === 'copied' ? tc('copied') : copyState === 'error' ? tc('copyError') : ''}
            {/* Closes the p interface element. */}
          </p>
          {/* Executes this line as the next step in the surrounding logic. */}
          {results ? (
            // Renders the section interface element or component.
            <section className="challenge-results" aria-labelledby="challenge-results-heading">
              {/* Renders the h3 interface element or component. */}
              <h3 id="challenge-results-heading">{t('resultsTitle')}</h3>
              {/* Renders the ChallengeResultBoard interface element or component. */}
              <ChallengeResultBoard
                /* Provides the results value to the surrounding call or element. */
                results={results}
                /* Provides the onPageChange value to the surrounding call or element. */
                onPageChange={(page) => {
                  // Calls setResults with the supplied values.
                  setResults(null);
                  // Calls setResultsError with the supplied values.
                  setResultsError(false);
                  // Calls setResultsPage with the supplied values.
                  setResultsPage(page);
                  // Closes the expression, call, or declaration started above.
                }}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Closes the section interface element. */}
            </section>
          ) : // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          resultsError ? (
            // Renders the p interface element or component.
            <p className="quiet-note">{t('resultsError')}</p>
          ) : (
            // Executes this line as the next step in the surrounding logic.
            // Renders the p interface element or component.
            <p className="quiet-note" role="status">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('loadingResults')}
              {/* Closes the p interface element. */}
            </p>
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
          ) : // Continues the surrounding operation with this required value or expression.
          // Executes this line as the next step in the surrounding logic.
          null}
          {/* Closes the section interface element. */}
        </section>
        {/* Executes this line as the next step in the surrounding logic. */}
        {managementPanel}
        {/* Closes the div interface element. */}
      </div>
      // Closes the expression, call, or declaration started above.
    );

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="content-stack">
      {/* Renders the form interface element or component. */}
      <form className="setup-form" onSubmit={(event) => void create(event)}>
        {/* Renders the label interface element or component. */}
        <label>
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('titleLabel')} <span className="quiet-note">({tc('optional')})</span>
          {/* Renders the input interface element or component. */}
          <input
            /* Provides the name value to the surrounding call or element. */
            name="challenge-title"
            /* Provides the autoComplete value to the surrounding call or element. */
            autoComplete="off"
            /* Provides the maxLength value to the surrounding call or element. */
            maxLength={80}
            /* Provides the value value to the surrounding call or element. */
            value={title}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => {
              // Calls setTitle with the supplied values.
              setTitle(event.target.value);
              // Executes this line as the next step in the surrounding logic.
              creationKeyRef.current = null;
              // Closes the expression, call, or declaration started above.
            }}
            /* Executes this line as the next step in the surrounding logic. */
            aria-describedby="challenge-title-hint"
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Renders the small interface element or component. */}
          <small id="challenge-title-hint">{t('titleHint')}</small>
          {/* Closes the label interface element. */}
        </label>
        {/* Renders the fieldset interface element or component. */}
        <fieldset className="choice-group">
          {/* Renders the legend interface element or component. */}
          <legend>{tp('difficulty')}</legend>
          {/* Renders the div interface element or component. */}
          <div className="segmented-options">
            {/* Executes this line as the next step in the surrounding logic. */}
            {(['easy', 'normal', 'hard', 'expert', 'custom'] as const).map((value) => (
              // Renders the label interface element or component.
              <label key={value}>
                {/* Renders the input interface element or component. */}
                <input
                  /* Provides the type value to the surrounding call or element. */
                  type="radio"
                  /* Provides the name value to the surrounding call or element. */
                  name="challenge-difficulty"
                  /* Provides the checked value to the surrounding call or element. */
                  checked={difficulty === value}
                  /* Provides the onChange value to the surrounding call or element. */
                  onChange={() => {
                    // Calls setDifficulty with the supplied values.
                    setDifficulty(value);
                    // Calls setSecret with the supplied values.
                    setSecret([]);
                    // Executes this line as the next step in the surrounding logic.
                    creationKeyRef.current = null;
                    // Closes the expression, call, or declaration started above.
                  }}
                  /* Executes this line as the next step in the surrounding logic. */
                />
                {/* Renders the span interface element or component. */}
                <span>{tp(value)}</span>
                {/* Closes the label interface element. */}
              </label>
              // Closes the expression, call, or declaration started above.
            ))}
            {/* Closes the div interface element. */}
          </div>
          {/* Closes the fieldset interface element. */}
        </fieldset>
        {/* Executes this line as the next step in the surrounding logic. */}
        {difficulty === 'custom' ? (
          // Renders the div interface element or component.
          <div className="form-grid panel">
            {/* Renders the label interface element or component. */}
            <label>
              {/* Executes this line as the next step in the surrounding logic. */}
              {tp('colours')}
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the type value to the surrounding call or element. */
                type="number"
                /* Provides the name value to the surrounding call or element. */
                name="challenge-colour-count"
                /* Provides the inputMode value to the surrounding call or element. */
                inputMode="numeric"
                /* Provides the min value to the surrounding call or element. */
                min="5"
                /* Provides the max value to the surrounding call or element. */
                max="10"
                /* Provides the value value to the surrounding call or element. */
                value={colourCount}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={(event) => {
                  // Calls setColourCount with the supplied values.
                  setColourCount(Number(event.target.value));
                  // Calls setSecret with the supplied values.
                  setSecret([]);
                  // Executes this line as the next step in the surrounding logic.
                  creationKeyRef.current = null;
                  // Closes the expression, call, or declaration started above.
                }}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Closes the label interface element. */}
            </label>
            {/* Renders the label interface element or component. */}
            <label>
              {/* Executes this line as the next step in the surrounding logic. */}
              {tp('codeLength')}
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the type value to the surrounding call or element. */
                type="number"
                /* Provides the name value to the surrounding call or element. */
                name="challenge-code-length"
                /* Provides the inputMode value to the surrounding call or element. */
                inputMode="numeric"
                /* Provides the min value to the surrounding call or element. */
                min="3"
                /* Provides the max value to the surrounding call or element. */
                max="6"
                /* Provides the value value to the surrounding call or element. */
                value={codeLength}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={(event) => {
                  // Calls setCodeLength with the supplied values.
                  setCodeLength(Number(event.target.value));
                  // Calls setSecret with the supplied values.
                  setSecret([]);
                  // Executes this line as the next step in the surrounding logic.
                  creationKeyRef.current = null;
                  // Closes the expression, call, or declaration started above.
                }}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Closes the label interface element. */}
            </label>
            {/* Renders the label interface element or component. */}
            <label>
              {/* Executes this line as the next step in the surrounding logic. */}
              {tp('maximumAttempts')}
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the type value to the surrounding call or element. */
                type="number"
                /* Provides the name value to the surrounding call or element. */
                name="challenge-max-attempts"
                /* Provides the inputMode value to the surrounding call or element. */
                inputMode="numeric"
                /* Provides the min value to the surrounding call or element. */
                min="1"
                /* Provides the max value to the surrounding call or element. */
                max="20"
                /* Provides the value value to the surrounding call or element. */
                value={maxAttempts}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={(event) => {
                  // Calls setMaxAttempts with the supplied values.
                  setMaxAttempts(Number(event.target.value));
                  // Executes this line as the next step in the surrounding logic.
                  creationKeyRef.current = null;
                  // Closes the expression, call, or declaration started above.
                }}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Closes the label interface element. */}
            </label>
            {/* Renders the label interface element or component. */}
            <label className="check-row">
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the type value to the surrounding call or element. */
                type="checkbox"
                /* Provides the name value to the surrounding call or element. */
                name="challenge-duplicates"
                /* Provides the checked value to the surrounding call or element. */
                checked={duplicatesAllowed}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={(event) => {
                  // Calls setDuplicatesAllowed with the supplied values.
                  setDuplicatesAllowed(event.target.checked);
                  // Calls setSecret with the supplied values.
                  setSecret([]);
                  // Executes this line as the next step in the surrounding logic.
                  creationKeyRef.current = null;
                  // Closes the expression, call, or declaration started above.
                }}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Renders the span interface element or component. */}
              <span>{tp('duplicates')}</span>
              {/* Closes the label interface element. */}
            </label>
            {/* Executes this line as the next step in the surrounding logic. */}
            {invalidCustom ? (
              // Renders the p interface element or component.
              <p className="inline-error" role="alert">
                {/* Executes this line as the next step in the surrounding logic. */}
                {tp('invalidCustom')}
                {/* Closes the p interface element. */}
              </p>
            ) : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            null}
            {/* Closes the div interface element. */}
          </div>
        ) : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        null}
        {/* Renders the fieldset interface element or component. */}
        <fieldset className="choice-group">
          {/* Renders the legend interface element or component. */}
          <legend>{t('secretMethod')}</legend>
          {/* Renders the div interface element or component. */}
          <div className="segmented-options">
            {/* Renders the label interface element or component. */}
            <label>
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the type value to the surrounding call or element. */
                type="radio"
                /* Provides the name value to the surrounding call or element. */
                name="secret-method"
                /* Provides the checked value to the surrounding call or element. */
                checked={!manual}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={() => {
                  // Calls setManual with the supplied values.
                  setManual(false);
                  // Calls setSecret with the supplied values.
                  setSecret([]);
                  // Executes this line as the next step in the surrounding logic.
                  creationKeyRef.current = null;
                  // Closes the expression, call, or declaration started above.
                }}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Renders the span interface element or component. */}
              <span>{t('generated')}</span>
              {/* Closes the label interface element. */}
            </label>
            {/* Renders the label interface element or component. */}
            <label>
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the type value to the surrounding call or element. */
                type="radio"
                /* Provides the name value to the surrounding call or element. */
                name="secret-method"
                /* Provides the checked value to the surrounding call or element. */
                checked={manual}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={() => {
                  // Calls setManual with the supplied values.
                  setManual(true);
                  // Calls setSecret with the supplied values.
                  setSecret([]);
                  // Executes this line as the next step in the surrounding logic.
                  creationKeyRef.current = null;
                  // Closes the expression, call, or declaration started above.
                }}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Renders the span interface element or component. */}
              <span>{t('manual')}</span>
              {/* Closes the label interface element. */}
            </label>
            {/* Closes the div interface element. */}
          </div>
          {/* Closes the fieldset interface element. */}
        </fieldset>
        {/* Executes this line as the next step in the surrounding logic. */}
        {manual ? (
          // Renders the fieldset interface element or component.
          <fieldset className="secret-picker panel">
            {/* Renders the legend interface element or component. */}
            <legend>{tp('secret')}</legend>
            {/* Renders the div interface element or component. */}
            <div className="secret-row" role="group" aria-label={tp('secret')}>
              {/* Begins the nested block or object completed below. */}
              {Array.from({ length: selectedRules.length }, (_, index) => {
                // Computes and stores colour for subsequent operations.
                const colour = secret[index];
                // Returns this result to the caller and ends the current function.
                return (
                  // Renders the span interface element or component.
                  <span
                    /* Provides the key value to the surrounding call or element. */
                    key={index}
                    /* Provides the className value to the surrounding call or element. */
                    className={`peg slot ${colour ? `peg-${colour}` : ''}`}
                    /* Provides the role value to the surrounding call or element. */
                    role="img"
                    /* Executes this line as the next step in the surrounding logic. */
                    aria-label={colour ? tg(`colors.${colour}`) : tg('empty')}
                    /* Closes the expression, call, or declaration started above. */
                  >
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {colour ? symbols[colour] : index + 1}
                    {/* Closes the span interface element. */}
                  </span>
                  // Closes the expression, call, or declaration started above.
                );
                // Closes the expression, call, or declaration started above.
              })}
              {/* Closes the div interface element. */}
            </div>
            {/* Renders the div interface element or component. */}
            <div className="palette">
              {/* Executes this line as the next step in the surrounding logic. */}
              {selectedRules.colours.map((colour) => (
                // Renders the button interface element or component.
                <button
                  /* Provides the key value to the surrounding call or element. */
                  key={colour}
                  /* Provides the className value to the surrounding call or element. */
                  className={`peg peg-${colour}`}
                  /* Provides the type value to the surrounding call or element. */
                  type="button"
                  /* Executes this line as the next step in the surrounding logic. */
                  aria-label={tg(`colors.${colour}`)}
                  /* Provides the onClick value to the surrounding call or element. */
                  onClick={() => {
                    // Calls setSecret with the supplied values.
                    setSecret(
                      /* Continues the surrounding operation with this required value or expression. */
                      (current) =>
                        // Executes this line as the next step in the surrounding logic.
                        !selectedRules.duplicates && current.includes(colour)
                          ? /* Continues the surrounding operation with this required value or expression. */
                            // Executes this line as the next step in the surrounding logic.
                            current
                          : /* Continues the surrounding operation with this required value or expression. */
                            // Supplies this item to the surrounding call or collection.
                            [...current, colour].slice(0, selectedRules.length),
                      // Closes the expression, call, or declaration started above.
                    );
                    // Executes this line as the next step in the surrounding logic.
                    creationKeyRef.current = null;
                    // Closes the expression, call, or declaration started above.
                  }}
                  /* Closes the expression, call, or declaration started above. */
                >
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {symbols[colour]}
                  {/* Closes the button interface element. */}
                </button>
                // Closes the expression, call, or declaration started above.
              ))}
              {/* Closes the div interface element. */}
            </div>
            {/* Renders the button interface element or component. */}
            <button
              /* Provides the className value to the surrounding call or element. */
              className="text-button"
              /* Provides the type value to the surrounding call or element. */
              type="button"
              /* Provides the disabled value to the surrounding call or element. */
              disabled={secret.length === 0}
              /* Provides the onClick value to the surrounding call or element. */
              onClick={() => {
                // Calls setSecret with the supplied values.
                setSecret((current) => current.slice(0, -1));
                // Executes this line as the next step in the surrounding logic.
                creationKeyRef.current = null;
                // Closes the expression, call, or declaration started above.
              }}
              /* Closes the expression, call, or declaration started above. */
            >
              {/* Executes this line as the next step in the surrounding logic. */}
              {tg('clear')}
              {/* Closes the button interface element. */}
            </button>
            {/* Renders the small interface element or component. */}
            <small>{tg('serverAuthoritative')}</small>
            {/* Closes the fieldset interface element. */}
          </fieldset>
        ) : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        null}
        {/* Renders the label interface element or component. */}
        <label className="check-row">
          {/* Renders the input interface element or component. */}
          <input
            /* Provides the type value to the surrounding call or element. */
            type="checkbox"
            /* Provides the name value to the surrounding call or element. */
            name="show-creator-name"
            /* Provides the checked value to the surrounding call or element. */
            checked={showCreatorName}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => {
              // Calls setShowCreatorName with the supplied values.
              setShowCreatorName(event.target.checked);
              // Executes this line as the next step in the surrounding logic.
              creationKeyRef.current = null;
              // Closes the expression, call, or declaration started above.
            }}
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Renders the span interface element or component. */}
          <span>{t('creatorVisible')}</span>
          {/* Closes the label interface element. */}
        </label>
        {/* Executes this line as the next step in the surrounding logic. */}
        {error ? (
          // Renders the p interface element or component.
          <p className="inline-error" role="alert">
            {/* Executes this line as the next step in the surrounding logic. */}
            {error}
            {/* Closes the p interface element. */}
          </p>
        ) : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        null}
        {/* Renders the button interface element or component. */}
        <button
          /* Provides the className value to the surrounding call or element. */
          className="button primary"
          /* Provides the type value to the surrounding call or element. */
          type="submit"
          /* Provides the disabled value to the surrounding call or element. */
          disabled={
            // Executes this line as the next step in the surrounding logic.
            submitting || invalidCustom || (manual && secret.length !== selectedRules.length)
            // Closes the expression, call, or declaration started above.
          }
          /* Closes the expression, call, or declaration started above. */
        >
          {/* Executes this line as the next step in the surrounding logic. */}
          {submitting ? t('creating') : t('create')}
          {/* Closes the button interface element. */}
        </button>
        {/* Closes the form interface element. */}
      </form>
      {/* Executes this line as the next step in the surrounding logic. */}
      {managementPanel}
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function ChallengePlayer({ shareCode }: { shareCode: string }) {
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Challenges');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Executes this line as the next step in the surrounding logic.
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Executes this line as the next step in the surrounding logic.
    api<Challenge>(`/v1/challenges/${encodeURIComponent(shareCode)}`)
      // Begins the nested block or object completed below.
      .then((value) => {
        // Checks this condition before running the nested branch.
        if (active) {
          // Calls setChallenge with the supplied values.
          setChallenge(value);
          // Calls setState with the supplied values.
          setState('ready');
          // Closes the expression, call, or declaration started above.
        }
        // Closes the expression, call, or declaration started above.
      })
      // Begins the nested block or object completed below.
      .catch(() => {
        // Checks this condition before running the nested branch.
        if (active) setState('error');
        // Closes the expression, call, or declaration started above.
      });
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api, shareCode]);

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the AsyncState interface element or component.
    <AsyncState
      /* Provides the state value to the surrounding call or element. */
      state={state}
      /* Provides the loadingLabel value to the surrounding call or element. */
      loadingLabel={tc('loading')}
      /* Provides the errorLabel value to the surrounding call or element. */
      errorLabel={t('loadError')}
      /* Provides the emptyLabel value to the surrounding call or element. */
      emptyLabel={t('expired')}
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Executes this line as the next step in the surrounding logic. */}
      {challenge && !challenge.revoked ? (
        // Renders the div interface element or component.
        <div className="challenge-layout">
          {/* Renders the section interface element or component. */}
          <section className="panel">
            {/* Renders the p interface element or component. */}
            <p className="mode-label">{t('playTitle')}</p>
            {/* Executes this line as the next step in the surrounding logic. */}
            {challenge.title ? <h2>{challenge.title}</h2> : null}
            {/* Executes this line as the next step in the surrounding logic. */}
            {challenge.creatorName ? (
              // Renders the p interface element or component.
              <p>
                {/* Begins the nested block or object completed below. */}
                {t('from', {
                  // Defines the name field in the surrounding object or type.
                  name:
                    // Executes this line as the next step in the surrounding logic.
                    challenge.creatorName === 'Anonymous breaker'
                      ? // Continues the surrounding operation with this required value or expression.
                        // Executes this line as the next step in the surrounding logic.
                        tc('anonymous')
                      : // Continues the surrounding operation with this required value or expression.
                        // Supplies this item to the surrounding call or collection.
                        challenge.creatorName,
                  // Closes the expression, call, or declaration started above.
                })}
                {/* Closes the p interface element. */}
              </p>
            ) : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            null}
            {/* Executes this line as the next step in the surrounding logic. */}
            {challenge.id ? (
              // Renders the p interface element or component.
              <p>{t('completedCount', { count: challenge.completedCount })}</p>
            ) : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            null}
            {/* Renders the h3 interface element or component. */}
            <h3>{t('rules')}</h3>
            {/* Renders the dl interface element or component. */}
            <dl className="rules-summary">
              {/* Renders the div interface element or component. */}
              <div>
                {/* Renders the dt interface element or component. */}
                <dt>{challenge.config.colours.length}</dt>
                {/* Renders the dd interface element or component. */}
                <dd>× {challenge.config.codeLength}</dd>
                {/* Closes the div interface element. */}
              </div>
              {/* Renders the div interface element or component. */}
              <div>
                {/* Renders the dt interface element or component. */}
                <dt>{challenge.config.maxAttempts}</dt>
                {/* Renders the dd interface element or component. */}
                <dd>{tc('attempts', { count: challenge.config.maxAttempts })}</dd>
                {/* Closes the div interface element. */}
              </div>
              {/* Closes the dl interface element. */}
            </dl>
            {/* Renders the p interface element or component. */}
            <p className="quiet-note">
              {/* Executes this line as the next step in the surrounding logic. */}
              {new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(
                // Supplies this item to the surrounding call or collection.
                new Date(challenge.expiresAt),
                // Closes the expression, call, or declaration started above.
              )}
              {/* Closes the p interface element. */}
            </p>
            {/* Closes the section interface element. */}
          </section>
          {/* Renders the GameBoard interface element or component. */}
          <GameBoard
            /* Provides the title value to the surrounding call or element. */
            title={challenge.title ?? t('playTitle')}
            /* Provides the startEndpoint value to the surrounding call or element. */
            startEndpoint={`/v1/challenges/${encodeURIComponent(shareCode)}/start`}
            /* Provides the startBody value to the surrounding call or element. */
            startBody={{ practice: false }}
            /* Provides the replayBody value to the surrounding call or element. */
            replayBody={{ practice: true }}
            /* Provides the replayLabel value to the surrounding call or element. */
            replayLabel={t('replay')}
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Closes the div interface element. */}
        </div>
      ) : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      null}
      {/* Closes the AsyncState interface element. */}
    </AsyncState>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
