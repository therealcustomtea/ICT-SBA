// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useLocale, useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useCallback, useEffect, useState } from 'react';
// Imports the dependency used by this module.
import { AsyncState } from '@/components/feature-page';
// Imports the dependency used by this module.
import { useApi } from '@/lib/api';

// Declares the Summary data shape or implementation.
type Summary = {
  // Defines the profiles field in the surrounding object or type.
  profiles: number;
  // Defines the activeGames field in the surrounding object or type.
  activeGames: number;
  // Defines the completedGames field in the surrounding object or type.
  completedGames: number;
  // Defines the activeRooms field in the surrounding object or type.
  activeRooms: number;
  // Defines the pendingReviewEntries field in the surrounding object or type.
  pendingReviewEntries: number;
  // Closes the expression, call, or declaration started above.
};
// Declares the Flag data shape or implementation.
type Flag = { key: string; enabled: boolean };
// Declares the Audit data shape or implementation.
type Audit = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Defines the actorId field in the surrounding object or type.
  actorId: string | null;
  // Defines the action field in the surrounding object or type.
  action: string;
  // Defines the targetType field in the surrounding object or type.
  targetType: string;
  // Defines the targetId field in the surrounding object or type.
  targetId: string;
  // Defines the reason field in the surrounding object or type.
  reason: string | null;
  // Defines the createdAt field in the surrounding object or type.
  createdAt: string;
  // Closes the expression, call, or declaration started above.
};
// Declares the AdminPage data shape or implementation.
type AdminPage<T> = { items: T[]; page: number; pageSize: number; total: number };
// Declares the AdminGame data shape or implementation.
type AdminGame = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Defines the ownerId field in the surrounding object or type.
  ownerId: string;
  // Defines the mode field in the surrounding object or type.
  mode: string;
  // Defines the status field in the surrounding object or type.
  status: string;
  // Defines the difficulty field in the surrounding object or type.
  difficulty: string | null;
  // Defines the attemptsUsed field in the surrounding object or type.
  attemptsUsed: number;
  // Defines the maxAttempts field in the surrounding object or type.
  maxAttempts: number;
  // Defines the score field in the surrounding object or type.
  score: number | null;
  // Defines the rankedEligibility field in the surrounding object or type.
  rankedEligibility: string;
  // Defines the startedAt field in the surrounding object or type.
  startedAt: string;
  // Defines the completedAt field in the surrounding object or type.
  completedAt: string | null;
  // Closes the expression, call, or declaration started above.
};
// Declares the AdminProfile data shape or implementation.
type AdminProfile = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Defines the displayName field in the surrounding object or type.
  displayName: string | null;
  // Defines the isAnonymous field in the surrounding object or type.
  isAnonymous: boolean;
  // Defines the publicLeaderboards field in the surrounding object or type.
  publicLeaderboards: boolean;
  // Defines the isBanned field in the surrounding object or type.
  isBanned: boolean;
  // Defines the deletedAt field in the surrounding object or type.
  deletedAt: string | null;
  // Defines the createdAt field in the surrounding object or type.
  createdAt: string;
  // Closes the expression, call, or declaration started above.
};
// Declares the AdminRoom data shape or implementation.
type AdminRoom = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Defines the status field in the surrounding object or type.
  status: string;
  // Defines the memberCount field in the surrounding object or type.
  memberCount: number;
  // Defines the winnerId field in the surrounding object or type.
  winnerId: string | null;
  // Defines the isTie field in the surrounding object or type.
  isTie: boolean;
  // Defines the expiresAt field in the surrounding object or type.
  expiresAt: string;
  // Defines the createdAt field in the surrounding object or type.
  createdAt: string;
  // Closes the expression, call, or declaration started above.
};
// Declares the AdminChallenge data shape or implementation.
type AdminChallenge = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Defines the creatorId field in the surrounding object or type.
  creatorId: string;
  // Defines the title field in the surrounding object or type.
  title: string | null;
  // Defines the completedCount field in the surrounding object or type.
  completedCount: number;
  // Defines the revokedAt field in the surrounding object or type.
  revokedAt: string | null;
  // Defines the expiresAt field in the surrounding object or type.
  expiresAt: string;
  // Defines the createdAt field in the surrounding object or type.
  createdAt: string;
  // Closes the expression, call, or declaration started above.
};
// Declares the AdminLeaderboard data shape or implementation.
type AdminLeaderboard = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Defines the gameId field in the surrounding object or type.
  gameId: string;
  // Defines the userId field in the surrounding object or type.
  userId: string;
  // Defines the category field in the surrounding object or type.
  category: string;
  // Defines the score field in the surrounding object or type.
  score: number;
  // Defines the attemptsUsed field in the surrounding object or type.
  attemptsUsed: number;
  // Defines the elapsedSeconds field in the surrounding object or type.
  elapsedSeconds: number;
  // Defines the reviewStatus field in the surrounding object or type.
  reviewStatus: string;
  // Defines the invalidatedAt field in the surrounding object or type.
  invalidatedAt: string | null;
  // Defines the completedAt field in the surrounding object or type.
  completedAt: string;
  // Closes the expression, call, or declaration started above.
};
// Declares the AdminAction data shape or implementation.
type AdminAction = 'invalidate' | 'restore' | 'restrict' | 'reverse' | 'revoke' | 'terminate';

// Exports this declaration for use by other modules.
export function AdminPanel() {
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Admin');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Executes this line as the next step in the surrounding logic.
  const [summary, setSummary] = useState<Summary | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [flags, setFlags] = useState<Flag[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [audit, setAudit] = useState<Audit[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [games, setGames] = useState<AdminGame[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [profiles, setProfiles] = useState<AdminProfile[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [rooms, setRooms] = useState<AdminRoom[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [challenges, setChallenges] = useState<AdminChallenge[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [leaderboard, setLeaderboard] = useState<AdminLeaderboard[]>([]);
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');
  // Executes this line as the next step in the surrounding logic.
  const [action, setAction] = useState<AdminAction>('invalidate');
  // Executes this line as the next step in the surrounding logic.
  const [target, setTarget] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [reason, setReason] = useState('');
  // Executes this line as the next step in the surrounding logic.
  const [pending, setPending] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [message, setMessage] = useState<string | null>(null);

  // Computes and stores load for subsequent operations.
  const load = useCallback(async () => {
    // Starts an operation whose expected failures are handled below.
    try {
      // Executes this line as the next step in the surrounding logic.
      const [
        // Supplies this item to the surrounding call or collection.
        nextSummary,
        // Supplies this item to the surrounding call or collection.
        nextFlags,
        // Supplies this item to the surrounding call or collection.
        nextAudit,
        // Supplies this item to the surrounding call or collection.
        nextGames,
        // Supplies this item to the surrounding call or collection.
        nextProfiles,
        // Supplies this item to the surrounding call or collection.
        nextRooms,
        // Supplies this item to the surrounding call or collection.
        nextChallenges,
        // Supplies this item to the surrounding call or collection.
        nextLeaderboard,
        // Executes this line as the next step in the surrounding logic.
      ] = await Promise.all([
        // Supplies this item to the surrounding call or collection.
        api<Summary>('/v1/admin/summary'),
        // Supplies this item to the surrounding call or collection.
        api<Flag[]>('/v1/admin/flags'),
        // Supplies this item to the surrounding call or collection.
        api<Audit[]>('/v1/admin/audit?limit=50'),
        // Supplies this item to the surrounding call or collection.
        api<AdminPage<AdminGame>>('/v1/admin/games?page=1&page_size=10'),
        // Supplies this item to the surrounding call or collection.
        api<AdminPage<AdminProfile>>('/v1/admin/profiles?page=1&page_size=10'),
        // Supplies this item to the surrounding call or collection.
        api<AdminPage<AdminRoom>>('/v1/admin/rooms?active_only=true&page=1&page_size=10'),
        // Supplies this item to the surrounding call or collection.
        api<AdminPage<AdminChallenge>>('/v1/admin/challenges?active_only=true&page=1&page_size=10'),
        // Supplies this item to the surrounding call or collection.
        api<AdminPage<AdminLeaderboard>>('/v1/admin/leaderboard-review?page=1&page_size=10'),
        // Closes the expression, call, or declaration started above.
      ]);
      // Calls setSummary with the supplied values.
      setSummary(nextSummary);
      // Calls setFlags with the supplied values.
      setFlags(nextFlags);
      // Calls setAudit with the supplied values.
      setAudit(nextAudit);
      // Calls setGames with the supplied values.
      setGames(nextGames.items);
      // Calls setProfiles with the supplied values.
      setProfiles(nextProfiles.items);
      // Calls setRooms with the supplied values.
      setRooms(nextRooms.items);
      // Calls setChallenges with the supplied values.
      setChallenges(nextChallenges.items);
      // Calls setLeaderboard with the supplied values.
      setLeaderboard(nextLeaderboard.items);
      // Calls setState with the supplied values.
      setState('ready');
      // Handles a failure from the protected operation.
    } catch {
      // Calls setState with the supplied values.
      setState('error');
      // Closes the expression, call, or declaration started above.
    }
    // Executes this line as the next step in the surrounding logic.
  }, [api]);
  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores frame for subsequent operations.
    const frame = requestAnimationFrame(() => void load());
    // Returns this result to the caller and ends the current function.
    return () => cancelAnimationFrame(frame);
    // Executes this line as the next step in the surrounding logic.
  }, [load]);

  // Computes and stores updateFlag for subsequent operations.
  const updateFlag = async (flag: Flag) => {
    // Calls setMessage with the supplied values.
    setMessage(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores updated for subsequent operations.
      const updated = await api<Flag>(`/v1/admin/flags/${encodeURIComponent(flag.key)}`, {
        // Defines the method field in the surrounding object or type.
        method: 'PATCH',
        // Defines the body field in the surrounding object or type.
        body: JSON.stringify({ enabled: !flag.enabled, reason: t('flagReason') }),
        // Closes the expression, call, or declaration started above.
      });
      // Calls setFlags with the supplied values.
      setFlags((current) => current.map((item) => (item.key === updated.key ? updated : item)));
      // Handles a failure from the protected operation.
    } catch {
      // Calls setMessage with the supplied values.
      setMessage(t('loadError'));
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };
  // Computes and stores apply for subsequent operations.
  const apply = async (event: React.FormEvent<HTMLFormElement>) => {
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Checks this condition before running the nested branch.
    if (!confirm(t('confirm'))) return;
    // Calls setPending with the supplied values.
    setPending(true);
    // Calls setMessage with the supplied values.
    setMessage(null);
    // Computes and stores routes for subsequent operations.
    const routes: Record<AdminAction, { path: string; body: Record<string, unknown> }> = {
      // Defines the invalidate field in the surrounding object or type.
      invalidate: { path: `/v1/admin/leaderboard/${target}/invalidate`, body: { reason } },
      // Defines the restore field in the surrounding object or type.
      restore: { path: `/v1/admin/leaderboard/${target}/restore`, body: { reason } },
      // Defines the restrict field in the surrounding object or type.
      restrict: { path: `/v1/admin/profiles/${target}/moderate`, body: { reason, enabled: true } },
      // Defines the reverse field in the surrounding object or type.
      reverse: { path: `/v1/admin/profiles/${target}/moderate`, body: { reason, enabled: false } },
      // Defines the revoke field in the surrounding object or type.
      revoke: { path: `/v1/admin/challenges/${target}/revoke`, body: { reason } },
      // Defines the terminate field in the surrounding object or type.
      terminate: { path: `/v1/admin/rooms/${target}/terminate`, body: { reason } },
      // Closes the expression, call, or declaration started above.
    };
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores selected for subsequent operations.
      const selected = routes[action];
      // Waits for this asynchronous operation to complete.
      await api(selected.path, { method: 'POST', body: JSON.stringify(selected.body) });
      // Calls setTarget with the supplied values.
      setTarget('');
      // Calls setReason with the supplied values.
      setReason('');
      // Calls setMessage with the supplied values.
      setMessage(t('actionApplied'));
      // Waits for this asynchronous operation to complete.
      await load();
      // Handles a failure from the protected operation.
    } catch {
      // Calls setMessage with the supplied values.
      setMessage(t('loadError'));
      // Runs cleanup regardless of the protected result.
    } finally {
      // Calls setPending with the supplied values.
      setPending(false);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the AsyncState interface element or component.
    <AsyncState
      /* Provides the state value to the surrounding call or element. */
      state={state}
      /* Provides the loadingLabel value to the surrounding call or element. */
      loadingLabel={tc('loading')}
      /* Provides the errorLabel value to the surrounding call or element. */
      errorLabel={t('unauthorized')}
      /* Provides the emptyLabel value to the surrounding call or element. */
      emptyLabel={t('empty')}
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Executes this line as the next step in the surrounding logic. */}
      {summary ? (
        // Renders the div interface element or component.
        <div className="admin-layout">
          {/* Renders the section interface element or component. */}
          <section aria-labelledby="metrics-heading">
            {/* Renders the h2 interface element or component. */}
            <h2 id="metrics-heading">{t('metrics')}</h2>
            {/* Renders the dl interface element or component. */}
            <dl className="stats-list">
              {/* Renders the Metric interface element or component. */}
              <Metric label={t('profiles')} value={summary.profiles} locale={locale} />
              {/* Renders the Metric interface element or component. */}
              <Metric label={t('activeGames')} value={summary.activeGames} locale={locale} />
              {/* Renders the Metric interface element or component. */}
              <Metric label={t('completedGames')} value={summary.completedGames} locale={locale} />
              {/* Renders the Metric interface element or component. */}
              <Metric label={t('activeRooms')} value={summary.activeRooms} locale={locale} />
              {/* Renders the Metric interface element or component. */}
              <Metric
                /* Provides the label value to the surrounding call or element. */
                label={t('pendingReview')}
                /* Provides the value value to the surrounding call or element. */
                value={summary.pendingReviewEntries}
                /* Provides the locale value to the surrounding call or element. */
                locale={locale}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Closes the dl interface element. */}
            </dl>
            {/* Closes the section interface element. */}
          </section>
          {/* Renders the section interface element or component. */}
          <section className="panel">
            {/* Renders the h2 interface element or component. */}
            <h2>{t('flags')}</h2>
            {/* Executes this line as the next step in the surrounding logic. */}
            {flags.length ? (
              // Renders the ul interface element or component.
              <ul className="flag-list">
                {/* Executes this line as the next step in the surrounding logic. */}
                {flags.map((flag) => (
                  // Renders the li interface element or component.
                  <li key={flag.key}>
                    {/* Renders the code interface element or component. */}
                    <code>{flag.key}</code>
                    {/* Renders the button interface element or component. */}
                    <button
                      /* Provides the className value to the surrounding call or element. */
                      className="button secondary"
                      /* Provides the type value to the surrounding call or element. */
                      type="button"
                      /* Executes this line as the next step in the surrounding logic. */
                      aria-pressed={flag.enabled}
                      /* Provides the onClick value to the surrounding call or element. */
                      onClick={() => void updateFlag(flag)}
                      /* Closes the expression, call, or declaration started above. */
                    >
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {flag.enabled ? t('enabled') : t('disabled')}
                      {/* Closes the button interface element. */}
                    </button>
                    {/* Closes the li interface element. */}
                  </li>
                  // Closes the expression, call, or declaration started above.
                ))}
                {/* Closes the ul interface element. */}
              </ul>
            ) : (
              // Executes this line as the next step in the surrounding logic.
              // Renders the p interface element or component.
              <p>{t('empty')}</p>
              // Closes the expression, call, or declaration started above.
            )}
            {/* Closes the section interface element. */}
          </section>
          {/* Renders the form interface element or component. */}
          <form className="panel form-stack" onSubmit={(event) => void apply(event)}>
            {/* Renders the h2 interface element or component. */}
            <h2>{t('action')}</h2>
            {/* Renders the label interface element or component. */}
            <label className="field">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('action')}
              {/* Renders the select interface element or component. */}
              <select
                /* Provides the name value to the surrounding call or element. */
                name="admin-action"
                /* Provides the autoComplete value to the surrounding call or element. */
                autoComplete="off"
                /* Provides the value value to the surrounding call or element. */
                value={action}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={(event) => setAction(event.target.value as AdminAction)}
                /* Closes the expression, call, or declaration started above. */
              >
                {/* Renders the option interface element or component. */}
                <option value="invalidate">{t('invalidate')}</option>
                {/* Renders the option interface element or component. */}
                <option value="restore">{t('restore')}</option>
                {/* Renders the option interface element or component. */}
                <option value="restrict">{t('restrict')}</option>
                {/* Renders the option interface element or component. */}
                <option value="reverse">{t('reverse')}</option>
                {/* Renders the option interface element or component. */}
                <option value="revoke">{t('revokeChallenge')}</option>
                {/* Renders the option interface element or component. */}
                <option value="terminate">{t('terminate')}</option>
                {/* Closes the select interface element. */}
              </select>
              {/* Closes the label interface element. */}
            </label>
            {/* Renders the label interface element or component. */}
            <label className="field">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('target')}
              {/* Renders the input interface element or component. */}
              <input
                /* Provides the name value to the surrounding call or element. */
                name="admin-target"
                /* Provides the autoComplete value to the surrounding call or element. */
                autoComplete="off"
                /* Provides the spellCheck value to the surrounding call or element. */
                spellCheck={false}
                /* Executes this line as the next step in the surrounding logic. */
                required
                /* Provides the value value to the surrounding call or element. */
                value={target}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={(event) => setTarget(event.target.value)}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Closes the label interface element. */}
            </label>
            {/* Renders the label interface element or component. */}
            <label className="field">
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('reason')}
              {/* Renders the textarea interface element or component. */}
              <textarea
                /* Provides the name value to the surrounding call or element. */
                name="admin-reason"
                /* Provides the autoComplete value to the surrounding call or element. */
                autoComplete="off"
                /* Executes this line as the next step in the surrounding logic. */
                required
                /* Provides the minLength value to the surrounding call or element. */
                minLength={3}
                /* Provides the maxLength value to the surrounding call or element. */
                maxLength={300}
                /* Provides the value value to the surrounding call or element. */
                value={reason}
                /* Provides the onChange value to the surrounding call or element. */
                onChange={(event) => setReason(event.target.value)}
                /* Executes this line as the next step in the surrounding logic. */
              />
              {/* Closes the label interface element. */}
            </label>
            {/* Renders the button interface element or component. */}
            <button className="button primary" disabled={pending}>
              {/* Executes this line as the next step in the surrounding logic. */}
              {t('apply')}
              {/* Closes the button interface element. */}
            </button>
            {/* Executes this line as the next step in the surrounding logic. */}
            {message ? <p role="status">{message}</p> : null}
            {/* Closes the form interface element. */}
          </form>
          {/* Renders the AdminRecords interface element or component. */}
          <AdminRecords
            /* Provides the games value to the surrounding call or element. */
            games={games}
            /* Provides the profiles value to the surrounding call or element. */
            profiles={profiles}
            /* Provides the rooms value to the surrounding call or element. */
            rooms={rooms}
            /* Provides the challenges value to the surrounding call or element. */
            challenges={challenges}
            /* Provides the leaderboard value to the surrounding call or element. */
            leaderboard={leaderboard}
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Renders the section interface element or component. */}
          <section>
            {/* Renders the h2 interface element or component. */}
            <h2>{t('audit')}</h2>
            {/* Executes this line as the next step in the surrounding logic. */}
            {audit.length ? (
              // Renders the div interface element or component.
              <div className="table-scroll">
                {/* Renders the table interface element or component. */}
                <table>
                  {/* Renders the caption interface element or component. */}
                  <caption className="sr-only">{t('audit')}</caption>
                  {/* Renders the thead interface element or component. */}
                  <thead>
                    {/* Renders the tr interface element or component. */}
                    <tr>
                      {/* Renders the th interface element or component. */}
                      <th scope="col">{t('action')}</th>
                      {/* Renders the th interface element or component. */}
                      <th scope="col">{t('target')}</th>
                      {/* Renders the th interface element or component. */}
                      <th scope="col">{t('reason')}</th>
                      {/* Renders the th interface element or component. */}
                      <th scope="col">{t('timestamp')}</th>
                      {/* Closes the tr interface element. */}
                    </tr>
                    {/* Closes the thead interface element. */}
                  </thead>
                  {/* Renders the tbody interface element or component. */}
                  <tbody>
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {audit.map((event) => (
                      // Renders the tr interface element or component.
                      <tr key={event.id}>
                        {/* Renders the td interface element or component. */}
                        <td>
                          {/* Renders the code interface element or component. */}
                          <code>{event.action}</code>
                          {/* Closes the td interface element. */}
                        </td>
                        {/* Renders the td interface element or component. */}
                        <td>
                          {/* Renders the code interface element or component. */}
                          <code>
                            {/* Executes this line as the next step in the surrounding logic. */}
                            {event.targetType}:{event.targetId}
                            {/* Closes the code interface element. */}
                          </code>
                          {/* Closes the td interface element. */}
                        </td>
                        {/* Renders the td interface element or component. */}
                        <td>{event.reason ?? '—'}</td>
                        {/* Renders the td interface element or component. */}
                        <td>
                          {/* Begins the nested block or object completed below. */}
                          {new Intl.DateTimeFormat(locale, {
                            // Defines the dateStyle field in the surrounding object or type.
                            dateStyle: 'medium',
                            // Defines the timeStyle field in the surrounding object or type.
                            timeStyle: 'short',
                            // Executes this line as the next step in the surrounding logic.
                          }).format(new Date(event.createdAt))}
                          {/* Closes the td interface element. */}
                        </td>
                        {/* Closes the tr interface element. */}
                      </tr>
                      // Closes the expression, call, or declaration started above.
                    ))}
                    {/* Closes the tbody interface element. */}
                  </tbody>
                  {/* Closes the table interface element. */}
                </table>
                {/* Closes the div interface element. */}
              </div>
            ) : (
              // Executes this line as the next step in the surrounding logic.
              // Renders the p interface element or component.
              <p>{t('empty')}</p>
              // Closes the expression, call, or declaration started above.
            )}
            {/* Closes the section interface element. */}
          </section>
          {/* Closes the div interface element. */}
        </div>
      ) : // Executes this line as the next step in the surrounding logic.
      null}
      {/* Closes the AsyncState interface element. */}
    </AsyncState>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Defines the Metric function and its callable behavior.
function Metric({ label, value, locale }: { label: string; value: number; locale: string }) {
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div>
      {/* Renders the dt interface element or component. */}
      <dt>{label}</dt>
      {/* Renders the dd interface element or component. */}
      <dd>{new Intl.NumberFormat(locale).format(value)}</dd>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Defines the AdminRecords function and its callable behavior.
function AdminRecords({
  // Supplies this item to the surrounding call or collection.
  games,
  // Supplies this item to the surrounding call or collection.
  profiles,
  // Supplies this item to the surrounding call or collection.
  rooms,
  // Supplies this item to the surrounding call or collection.
  challenges,
  // Supplies this item to the surrounding call or collection.
  leaderboard,
  // Begins the nested block or object completed below.
}: {
  // Defines the games field in the surrounding object or type.
  games: AdminGame[];
  // Defines the profiles field in the surrounding object or type.
  profiles: AdminProfile[];
  // Defines the rooms field in the surrounding object or type.
  rooms: AdminRoom[];
  // Defines the challenges field in the surrounding object or type.
  challenges: AdminChallenge[];
  // Defines the leaderboard field in the surrounding object or type.
  leaderboard: AdminLeaderboard[];
  // Begins the nested block or object completed below.
}) {
  // Computes and stores locale for subsequent operations.
  const locale = useLocale();
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Admin');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores timestamp for subsequent operations.
  const timestamp = (value: string) =>
    // Executes this line as the next step in the surrounding logic.
    new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(
      // Supplies this item to the surrounding call or collection.
      new Date(value),
      // Closes the expression, call, or declaration started above.
    );
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="admin-records">
      {/* Renders the RecordSection interface element or component. */}
      <RecordSection title={t('games')} empty={t('empty')}>
        {/* Renders the ul interface element or component. */}
        <ul className="history-list">
          {/* Executes this line as the next step in the surrounding logic. */}
          {games.map((game) => (
            // Renders the li interface element or component.
            <li key={game.id}>
              {/* Renders the code interface element or component. */}
              <code>{game.id}</code>
              {/* Renders the span interface element or component. */}
              <span>
                {/* Executes this line as the next step in the surrounding logic. */}
                {game.mode} · {game.status}
                {/* Closes the span interface element. */}
              </span>
              {/* Renders the span interface element or component. */}
              <span>
                {/* Executes this line as the next step in the surrounding logic. */}
                {game.attemptsUsed}/{game.maxAttempts}
                {/* Closes the span interface element. */}
              </span>
              {/* Renders the time interface element or component. */}
              <time dateTime={game.startedAt}>{timestamp(game.startedAt)}</time>
              {/* Closes the li interface element. */}
            </li>
            // Closes the expression, call, or declaration started above.
          ))}
          {/* Closes the ul interface element. */}
        </ul>
        {/* Closes the RecordSection interface element. */}
      </RecordSection>
      {/* Renders the RecordSection interface element or component. */}
      <RecordSection title={t('users')} empty={t('empty')}>
        {/* Renders the ul interface element or component. */}
        <ul className="history-list">
          {/* Executes this line as the next step in the surrounding logic. */}
          {profiles.map((profile) => (
            // Renders the li interface element or component.
            <li key={profile.id}>
              {/* Renders the code interface element or component. */}
              <code>{profile.id}</code>
              {/* Renders the span interface element or component. */}
              <span>{profile.displayName ?? tc('anonymous')}</span>
              {/* Renders the span interface element or component. */}
              <span>{profile.isBanned ? t('restricted') : t('clear')}</span>
              {/* Renders the time interface element or component. */}
              <time dateTime={profile.createdAt}>{timestamp(profile.createdAt)}</time>
              {/* Closes the li interface element. */}
            </li>
            // Closes the expression, call, or declaration started above.
          ))}
          {/* Closes the ul interface element. */}
        </ul>
        {/* Closes the RecordSection interface element. */}
      </RecordSection>
      {/* Renders the RecordSection interface element or component. */}
      <RecordSection title={t('rooms')} empty={t('empty')}>
        {/* Renders the ul interface element or component. */}
        <ul className="history-list">
          {/* Executes this line as the next step in the surrounding logic. */}
          {rooms.map((room) => (
            // Renders the li interface element or component.
            <li key={room.id}>
              {/* Renders the code interface element or component. */}
              <code>{room.id}</code>
              {/* Renders the span interface element or component. */}
              <span>{room.status}</span>
              {/* Renders the span interface element or component. */}
              <span>{t('memberCount', { count: room.memberCount })}</span>
              {/* Renders the time interface element or component. */}
              <time dateTime={room.expiresAt}>{timestamp(room.expiresAt)}</time>
              {/* Closes the li interface element. */}
            </li>
            // Closes the expression, call, or declaration started above.
          ))}
          {/* Closes the ul interface element. */}
        </ul>
        {/* Closes the RecordSection interface element. */}
      </RecordSection>
      {/* Renders the RecordSection interface element or component. */}
      <RecordSection title={t('challenges')} empty={t('empty')}>
        {/* Renders the ul interface element or component. */}
        <ul className="history-list">
          {/* Executes this line as the next step in the surrounding logic. */}
          {challenges.map((challenge) => (
            // Renders the li interface element or component.
            <li key={challenge.id}>
              {/* Renders the code interface element or component. */}
              <code>{challenge.id}</code>
              {/* Renders the span interface element or component. */}
              <span>{challenge.title ?? t('untitled')}</span>
              {/* Renders the span interface element or component. */}
              <span>{t('completionCount', { count: challenge.completedCount })}</span>
              {/* Renders the time interface element or component. */}
              <time dateTime={challenge.expiresAt}>{timestamp(challenge.expiresAt)}</time>
              {/* Closes the li interface element. */}
            </li>
            // Closes the expression, call, or declaration started above.
          ))}
          {/* Closes the ul interface element. */}
        </ul>
        {/* Closes the RecordSection interface element. */}
      </RecordSection>
      {/* Renders the RecordSection interface element or component. */}
      <RecordSection title={t('leaderboards')} empty={t('empty')}>
        {/* Renders the ul interface element or component. */}
        <ul className="history-list">
          {/* Executes this line as the next step in the surrounding logic. */}
          {leaderboard.map((entry) => (
            // Renders the li interface element or component.
            <li key={entry.id}>
              {/* Renders the code interface element or component. */}
              <code>{entry.id}</code>
              {/* Renders the span interface element or component. */}
              <span>
                {/* Executes this line as the next step in the surrounding logic. */}
                {entry.category} · {entry.reviewStatus}
                {/* Closes the span interface element. */}
              </span>
              {/* Renders the span interface element or component. */}
              <span>{new Intl.NumberFormat(locale).format(entry.score)}</span>
              {/* Renders the time interface element or component. */}
              <time dateTime={entry.completedAt}>{timestamp(entry.completedAt)}</time>
              {/* Closes the li interface element. */}
            </li>
            // Closes the expression, call, or declaration started above.
          ))}
          {/* Closes the ul interface element. */}
        </ul>
        {/* Closes the RecordSection interface element. */}
      </RecordSection>
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Defines the RecordSection function and its callable behavior.
function RecordSection({
  // Supplies this item to the surrounding call or collection.
  title,
  // Supplies this item to the surrounding call or collection.
  empty,
  // Supplies this item to the surrounding call or collection.
  children,
  // Begins the nested block or object completed below.
}: {
  // Defines the title field in the surrounding object or type.
  title: string;
  // Defines the empty field in the surrounding object or type.
  empty: string;
  // Defines the children field in the surrounding object or type.
  children: React.ReactElement<{ children?: React.ReactNode }>;
  // Begins the nested block or object completed below.
}) {
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the section interface element or component.
    <section className="panel">
      {/* Renders the h2 interface element or component. */}
      <h2>{title}</h2>
      {/* Executes this line as the next step in the surrounding logic. */}
      {children.props.children &&
      // Calls Array.isArray with the supplied values.
      Array.isArray(children.props.children) &&
      // Executes this line as the next step in the surrounding logic.
      children.props.children.length === 0 ? (
        // Renders the p interface element or component.
        <p>{empty}</p>
      ) : (
        // Executes this line as the next step in the surrounding logic.
        // Executes this line as the next step in the surrounding logic.
        children
        // Closes the expression, call, or declaration started above.
      )}
      {/* Closes the section interface element. */}
    </section>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}
