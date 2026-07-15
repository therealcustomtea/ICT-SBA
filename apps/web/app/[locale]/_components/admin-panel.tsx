'use client';

import { useLocale, useTranslations } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { AsyncState } from '@/components/feature-page';
import { useApi } from '@/lib/api';

type Summary = {
  profiles: number;
  activeGames: number;
  completedGames: number;
  activeRooms: number;
  pendingReviewEntries: number;
};
type Flag = { key: string; enabled: boolean };
type Audit = {
  id: string;
  actorId: string | null;
  action: string;
  targetType: string;
  targetId: string;
  reason: string | null;
  createdAt: string;
};
type AdminPage<T> = { items: T[]; page: number; pageSize: number; total: number };
type AdminGame = {
  id: string;
  ownerId: string;
  mode: string;
  status: string;
  difficulty: string | null;
  attemptsUsed: number;
  maxAttempts: number;
  score: number | null;
  rankedEligibility: string;
  startedAt: string;
  completedAt: string | null;
};
type AdminProfile = {
  id: string;
  displayName: string | null;
  isAnonymous: boolean;
  publicLeaderboards: boolean;
  isBanned: boolean;
  deletedAt: string | null;
  createdAt: string;
};
type AdminRoom = {
  id: string;
  status: string;
  memberCount: number;
  winnerId: string | null;
  isTie: boolean;
  expiresAt: string;
  createdAt: string;
};
type AdminChallenge = {
  id: string;
  creatorId: string;
  title: string | null;
  completedCount: number;
  revokedAt: string | null;
  expiresAt: string;
  createdAt: string;
};
type AdminLeaderboard = {
  id: string;
  gameId: string;
  userId: string;
  category: string;
  score: number;
  attemptsUsed: number;
  elapsedSeconds: number;
  reviewStatus: string;
  invalidatedAt: string | null;
  completedAt: string;
};
type AdminAction = 'invalidate' | 'restore' | 'restrict' | 'reverse' | 'revoke' | 'terminate';

export function AdminPanel() {
  const locale = useLocale();
  const t = useTranslations('Admin');
  const tc = useTranslations('Common');
  const api = useApi();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [flags, setFlags] = useState<Flag[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [games, setGames] = useState<AdminGame[]>([]);
  const [profiles, setProfiles] = useState<AdminProfile[]>([]);
  const [rooms, setRooms] = useState<AdminRoom[]>([]);
  const [challenges, setChallenges] = useState<AdminChallenge[]>([]);
  const [leaderboard, setLeaderboard] = useState<AdminLeaderboard[]>([]);
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');
  const [action, setAction] = useState<AdminAction>('invalidate');
  const [target, setTarget] = useState('');
  const [reason, setReason] = useState('');
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [
        nextSummary,
        nextFlags,
        nextAudit,
        nextGames,
        nextProfiles,
        nextRooms,
        nextChallenges,
        nextLeaderboard,
      ] = await Promise.all([
        api<Summary>('/v1/admin/summary'),
        api<Flag[]>('/v1/admin/flags'),
        api<Audit[]>('/v1/admin/audit?limit=50'),
        api<AdminPage<AdminGame>>('/v1/admin/games?page=1&page_size=10'),
        api<AdminPage<AdminProfile>>('/v1/admin/profiles?page=1&page_size=10'),
        api<AdminPage<AdminRoom>>('/v1/admin/rooms?active_only=true&page=1&page_size=10'),
        api<AdminPage<AdminChallenge>>('/v1/admin/challenges?active_only=true&page=1&page_size=10'),
        api<AdminPage<AdminLeaderboard>>('/v1/admin/leaderboard-review?page=1&page_size=10'),
      ]);
      setSummary(nextSummary);
      setFlags(nextFlags);
      setAudit(nextAudit);
      setGames(nextGames.items);
      setProfiles(nextProfiles.items);
      setRooms(nextRooms.items);
      setChallenges(nextChallenges.items);
      setLeaderboard(nextLeaderboard.items);
      setState('ready');
    } catch {
      setState('error');
    }
  }, [api]);
  useEffect(() => {
    const frame = requestAnimationFrame(() => void load());
    return () => cancelAnimationFrame(frame);
  }, [load]);

  const updateFlag = async (flag: Flag) => {
    setMessage(null);
    try {
      const updated = await api<Flag>(`/v1/admin/flags/${encodeURIComponent(flag.key)}`, {
        method: 'PATCH',
        body: JSON.stringify({ enabled: !flag.enabled, reason: t('flagReason') }),
      });
      setFlags((current) => current.map((item) => (item.key === updated.key ? updated : item)));
    } catch {
      setMessage(t('loadError'));
    }
  };
  const apply = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!confirm(t('confirm'))) return;
    setPending(true);
    setMessage(null);
    const routes: Record<AdminAction, { path: string; body: Record<string, unknown> }> = {
      invalidate: { path: `/v1/admin/leaderboard/${target}/invalidate`, body: { reason } },
      restore: { path: `/v1/admin/leaderboard/${target}/restore`, body: { reason } },
      restrict: { path: `/v1/admin/profiles/${target}/moderate`, body: { reason, enabled: true } },
      reverse: { path: `/v1/admin/profiles/${target}/moderate`, body: { reason, enabled: false } },
      revoke: { path: `/v1/admin/challenges/${target}/revoke`, body: { reason } },
      terminate: { path: `/v1/admin/rooms/${target}/terminate`, body: { reason } },
    };
    try {
      const selected = routes[action];
      await api(selected.path, { method: 'POST', body: JSON.stringify(selected.body) });
      setTarget('');
      setReason('');
      setMessage(t('actionApplied'));
      await load();
    } catch {
      setMessage(t('loadError'));
    } finally {
      setPending(false);
    }
  };

  return (
    <AsyncState
      state={state}
      loadingLabel={tc('loading')}
      errorLabel={t('unauthorized')}
      emptyLabel={t('empty')}
    >
      {summary ? (
        <div className="admin-layout">
          <section aria-labelledby="metrics-heading">
            <h2 id="metrics-heading">{t('metrics')}</h2>
            <dl className="stats-list">
              <Metric label={t('profiles')} value={summary.profiles} locale={locale} />
              <Metric label={t('activeGames')} value={summary.activeGames} locale={locale} />
              <Metric label={t('completedGames')} value={summary.completedGames} locale={locale} />
              <Metric label={t('activeRooms')} value={summary.activeRooms} locale={locale} />
              <Metric
                label={t('pendingReview')}
                value={summary.pendingReviewEntries}
                locale={locale}
              />
            </dl>
          </section>
          <section className="panel">
            <h2>{t('flags')}</h2>
            {flags.length ? (
              <ul className="flag-list">
                {flags.map((flag) => (
                  <li key={flag.key}>
                    <code>{flag.key}</code>
                    <button
                      className="button secondary"
                      type="button"
                      aria-pressed={flag.enabled}
                      onClick={() => void updateFlag(flag)}
                    >
                      {flag.enabled ? t('enabled') : t('disabled')}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p>{t('empty')}</p>
            )}
          </section>
          <form className="panel form-stack" onSubmit={(event) => void apply(event)}>
            <h2>{t('action')}</h2>
            <label className="field">
              {t('action')}
              <select
                name="admin-action"
                autoComplete="off"
                value={action}
                onChange={(event) => setAction(event.target.value as AdminAction)}
              >
                <option value="invalidate">{t('invalidate')}</option>
                <option value="restore">{t('restore')}</option>
                <option value="restrict">{t('restrict')}</option>
                <option value="reverse">{t('reverse')}</option>
                <option value="revoke">{t('revokeChallenge')}</option>
                <option value="terminate">{t('terminate')}</option>
              </select>
            </label>
            <label className="field">
              {t('target')}
              <input
                name="admin-target"
                autoComplete="off"
                spellCheck={false}
                required
                value={target}
                onChange={(event) => setTarget(event.target.value)}
              />
            </label>
            <label className="field">
              {t('reason')}
              <textarea
                name="admin-reason"
                autoComplete="off"
                required
                minLength={3}
                maxLength={300}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
              />
            </label>
            <button className="button primary" disabled={pending}>
              {t('apply')}
            </button>
            {message ? <p role="status">{message}</p> : null}
          </form>
          <AdminRecords
            games={games}
            profiles={profiles}
            rooms={rooms}
            challenges={challenges}
            leaderboard={leaderboard}
          />
          <section>
            <h2>{t('audit')}</h2>
            {audit.length ? (
              <div className="table-scroll">
                <table>
                  <caption className="sr-only">{t('audit')}</caption>
                  <thead>
                    <tr>
                      <th scope="col">{t('action')}</th>
                      <th scope="col">{t('target')}</th>
                      <th scope="col">{t('reason')}</th>
                      <th scope="col">{t('timestamp')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {audit.map((event) => (
                      <tr key={event.id}>
                        <td>
                          <code>{event.action}</code>
                        </td>
                        <td>
                          <code>
                            {event.targetType}:{event.targetId}
                          </code>
                        </td>
                        <td>{event.reason ?? '—'}</td>
                        <td>
                          {new Intl.DateTimeFormat(locale, {
                            dateStyle: 'medium',
                            timeStyle: 'short',
                          }).format(new Date(event.createdAt))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>{t('empty')}</p>
            )}
          </section>
        </div>
      ) : null}
    </AsyncState>
  );
}

function Metric({ label, value, locale }: { label: string; value: number; locale: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{new Intl.NumberFormat(locale).format(value)}</dd>
    </div>
  );
}

function AdminRecords({
  games,
  profiles,
  rooms,
  challenges,
  leaderboard,
}: {
  games: AdminGame[];
  profiles: AdminProfile[];
  rooms: AdminRoom[];
  challenges: AdminChallenge[];
  leaderboard: AdminLeaderboard[];
}) {
  const locale = useLocale();
  const t = useTranslations('Admin');
  const tc = useTranslations('Common');
  const timestamp = (value: string) =>
    new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(
      new Date(value),
    );
  return (
    <div className="admin-records">
      <RecordSection title={t('games')} empty={t('empty')}>
        <ul className="history-list">
          {games.map((game) => (
            <li key={game.id}>
              <code>{game.id}</code>
              <span>
                {game.mode} · {game.status}
              </span>
              <span>
                {game.attemptsUsed}/{game.maxAttempts}
              </span>
              <time dateTime={game.startedAt}>{timestamp(game.startedAt)}</time>
            </li>
          ))}
        </ul>
      </RecordSection>
      <RecordSection title={t('users')} empty={t('empty')}>
        <ul className="history-list">
          {profiles.map((profile) => (
            <li key={profile.id}>
              <code>{profile.id}</code>
              <span>{profile.displayName ?? tc('anonymous')}</span>
              <span>{profile.isBanned ? t('restricted') : t('clear')}</span>
              <time dateTime={profile.createdAt}>{timestamp(profile.createdAt)}</time>
            </li>
          ))}
        </ul>
      </RecordSection>
      <RecordSection title={t('rooms')} empty={t('empty')}>
        <ul className="history-list">
          {rooms.map((room) => (
            <li key={room.id}>
              <code>{room.id}</code>
              <span>{room.status}</span>
              <span>{t('memberCount', { count: room.memberCount })}</span>
              <time dateTime={room.expiresAt}>{timestamp(room.expiresAt)}</time>
            </li>
          ))}
        </ul>
      </RecordSection>
      <RecordSection title={t('challenges')} empty={t('empty')}>
        <ul className="history-list">
          {challenges.map((challenge) => (
            <li key={challenge.id}>
              <code>{challenge.id}</code>
              <span>{challenge.title ?? t('untitled')}</span>
              <span>{t('completionCount', { count: challenge.completedCount })}</span>
              <time dateTime={challenge.expiresAt}>{timestamp(challenge.expiresAt)}</time>
            </li>
          ))}
        </ul>
      </RecordSection>
      <RecordSection title={t('leaderboards')} empty={t('empty')}>
        <ul className="history-list">
          {leaderboard.map((entry) => (
            <li key={entry.id}>
              <code>{entry.id}</code>
              <span>
                {entry.category} · {entry.reviewStatus}
              </span>
              <span>{new Intl.NumberFormat(locale).format(entry.score)}</span>
              <time dateTime={entry.completedAt}>{timestamp(entry.completedAt)}</time>
            </li>
          ))}
        </ul>
      </RecordSection>
    </div>
  );
}

function RecordSection({
  title,
  empty,
  children,
}: {
  title: string;
  empty: string;
  children: React.ReactElement<{ children?: React.ReactNode }>;
}) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {children.props.children &&
      Array.isArray(children.props.children) &&
      children.props.children.length === 0 ? (
        <p>{empty}</p>
      ) : (
        children
      )}
    </section>
  );
}
