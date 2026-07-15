'use client';

import { useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useRef, useState } from 'react';
import { AsyncState } from '@/components/feature-page';
import { useSession } from '@/components/session-provider';
import { Link, useRouter } from '@/i18n/navigation';
import { API_ORIGIN, type Attempt, type Game, type Room, useApi } from '@/lib/api';
import { useProductAnalytics } from '@/lib/use-product-analytics';

type RoomMember = {
  userId: string;
  displayName: string;
  connected: boolean;
  ready: boolean;
  attemptsUsed: number;
  completed: boolean;
  gameId: string | null;
};
type LobbyRoom = Omit<Room, 'members'> & { members: RoomMember[] };
type DuelRoom = Omit<LobbyRoom, 'roomCode'> & { roomCode: string };
type PendingDuelGuess = { guess: string[]; idempotencyKey: string };
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
const roomInviteStorageKey = (roomId: string) => `cipherboard:room-invite:${roomId}`;
const duelRowStorageKey = (roomId: string) => `cipherboard:duel-row:${roomId}`;
const duelPendingStorageKey = (roomId: string) => `cipherboard:duel-pending:${roomId}`;
const analyticsRoomState = (status: string) =>
  status === 'active' || status === 'completed' || status === 'expired' || status === 'terminated'
    ? status
    : 'waiting';
const withReadyMembers = (room: Room): LobbyRoom => ({
  ...room,
  members: room.members.map((member) => ({
    ...member,
    ready: Boolean('ready' in member && member.ready),
  })),
});

export function RoomEntry() {
  const t = useTranslations('Rooms');
  const tp = useTranslations('Play');
  const api = useApi();
  const analytics = useProductAnalytics();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [difficulty, setDifficulty] = useState<'easy' | 'normal' | 'hard' | 'expert'>('normal');
  const [code, setCode] = useState(() => searchParams.get('code') ?? '');
  const [pending, setPending] = useState<'create' | 'join' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const roomCreationKeyRef = useRef<string | null>(null);

  const create = async () => {
    setPending('create');
    setError(null);
    try {
      roomCreationKeyRef.current ??= crypto.randomUUID();
      const room = await api<Room>('/v1/rooms', {
        method: 'POST',
        body: JSON.stringify({ difficulty, idempotencyKey: roomCreationKeyRef.current }),
      });
      if (!room.roomCode) throw new Error('ROOM_INVITE_MISSING');
      sessionStorage.setItem(roomInviteStorageKey(room.id), room.roomCode);
      analytics('room_joined', { roomState: analyticsRoomState(room.status), reconnect: false });
      router.push(`/rooms/${room.id}`);
    } catch {
      setError(t('roomError'));
      setPending(null);
    }
  };
  const join = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPending('join');
    setError(null);
    try {
      const room = await api<Room>(`/v1/rooms/${encodeURIComponent(code.trim())}/join`, {
        method: 'POST',
      });
      analytics('room_joined', { roomState: analyticsRoomState(room.status), reconnect: false });
      router.push(`/rooms/${room.id}`);
    } catch {
      setError(t('roomError'));
      setPending(null);
    }
  };

  return (
    <div className="room-entry-layout">
      <section className="panel">
        <h2>{t('create')}</h2>
        <fieldset className="choice-group">
          <legend>{tp('difficulty')}</legend>
          <div className="segmented-options">
            {(['easy', 'normal', 'hard', 'expert'] as const).map((value) => (
              <label key={value}>
                <input
                  type="radio"
                  name="room-difficulty"
                  checked={difficulty === value}
                  onChange={() => {
                    setDifficulty(value);
                    roomCreationKeyRef.current = null;
                  }}
                />
                <span>{tp(value)}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <button
          type="button"
          className="button primary"
          disabled={pending !== null}
          onClick={() => void create()}
        >
          {pending === 'create' ? t('creating') : t('create')}
        </button>
      </section>
      <form className="panel" onSubmit={(event) => void join(event)}>
        <h2>{t('join')}</h2>
        <label>
          {t('inviteCode')}
          <input
            name="invite-code"
            autoComplete="off"
            spellCheck={false}
            value={code}
            onChange={(event) => setCode(event.target.value)}
            required
            minLength={20}
            maxLength={64}
            pattern="[A-Za-z0-9_-]+"
            autoCapitalize="none"
            aria-describedby="invite-hint"
          />
        </label>
        <small id="invite-hint">{t('inviteHint')}</small>
        <button className="button secondary" disabled={pending !== null}>
          {pending === 'join' ? t('joining') : t('join')}
        </button>
      </form>
      {error ? (
        <p className="inline-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function RoomLobby({ roomId }: { roomId: string }) {
  const t = useTranslations('Rooms');
  const tc = useTranslations('Common');
  const api = useApi();
  const { user } = useSession();
  const [room, setRoom] = useState<LobbyRoom | null>(null);
  const [createdRoomCode] = useState<string | null>(() =>
    typeof window === 'undefined' ? null : sessionStorage.getItem(roomInviteStorageKey(roomId)),
  );
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');
  const [readyPending, setReadyPending] = useState(false);
  const [readyError, setReadyError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const refresh = () =>
      api<Room>(`/v1/rooms/${encodeURIComponent(roomId)}`)
        .then((value) => {
          if (active) {
            setRoom(withReadyMembers(value));
            setState('ready');
          }
        })
        .catch(() => {
          if (active) setState('error');
        });
    void refresh();
    const timer = setInterval(refresh, 3000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [api, roomId]);

  const roomCode = createdRoomCode ?? room?.roomCode ?? null;
  const inviteUrl =
    roomCode && typeof window !== 'undefined'
      ? `${window.location.origin}/${window.location.pathname.split('/')[1]}/rooms?code=${roomCode}`
      : '';
  const copyInvite = async () => {
    if (!inviteUrl) return;
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setCopyState('copied');
    } catch {
      setCopyState('error');
    }
  };
  const markReady = async () => {
    setReadyPending(true);
    setReadyError(null);
    try {
      const nextRoom = await api<Room>(`/v1/rooms/${encodeURIComponent(roomId)}/ready`, {
        method: 'POST',
      });
      setRoom(withReadyMembers(nextRoom));
    } catch {
      setReadyError(t('roomError'));
    } finally {
      setReadyPending(false);
    }
  };
  const currentMember = room?.members.find((member) => member.userId === user?.id) ?? null;
  return (
    <AsyncState
      state={state}
      loadingLabel={tc('loading')}
      errorLabel={t('roomError')}
      emptyLabel={t('expired')}
    >
      {room ? (
        <div className="lobby-layout">
          <section className="panel">
            {roomCode ? (
              <>
                <p className="mode-label">{t('roomCode', { code: roomCode })}</p>
                <h2>{t('invite')}</h2>
                <label>
                  {t('inviteCode')}
                  <input
                    name="invite-url"
                    autoComplete="off"
                    spellCheck={false}
                    readOnly
                    value={inviteUrl}
                  />
                </label>
                <button
                  className="button secondary"
                  type="button"
                  onClick={() => void copyInvite()}
                >
                  {copyState === 'copied' ? tc('copied') : tc('copy')}
                </button>
                <p
                  className="sr-only"
                  role={copyState === 'error' ? 'alert' : 'status'}
                  aria-live="polite"
                >
                  {copyState === 'copied'
                    ? tc('copied')
                    : copyState === 'error'
                      ? tc('copyError')
                      : ''}
                </p>
              </>
            ) : (
              <p className="quiet-note">{t('inviteUnavailable')}</p>
            )}
          </section>
          <section className="panel">
            <h2>{t('players')}</h2>
            <ul className="member-list">
              {room.members.map((member) => (
                <li key={member.userId}>
                  <span>
                    {member.displayName === 'Anonymous breaker'
                      ? tc('anonymous')
                      : member.displayName}
                  </span>
                  <span className="member-state">
                    <span className={member.ready ? 'status success' : 'status muted'}>
                      {member.ready ? t('ready') : t('notReady')}
                    </span>
                    <span className={member.connected ? 'status success' : 'status muted'}>
                      {member.connected ? t('connected') : t('disconnected')}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
            {room.status === 'waiting' ? (
              <>
                <p role="status">{room.members.length < 2 ? t('waiting') : t('waitingForReady')}</p>
                {currentMember && !currentMember.ready ? (
                  <button
                    className="button primary"
                    type="button"
                    disabled={readyPending}
                    onClick={() => void markReady()}
                  >
                    {readyPending ? t('markingReady') : t('markReady')}
                  </button>
                ) : currentMember?.ready ? (
                  <p className="notice success" role="status">
                    {t('youAreReady')}
                  </p>
                ) : null}
              </>
            ) : (
              <Link className="button primary" href={`/rooms/${room.id}/duel`}>
                {t('start')}
              </Link>
            )}
            {readyError ? (
              <p className="inline-error" role="alert">
                {readyError}
              </p>
            ) : null}
          </section>
        </div>
      ) : null}
    </AsyncState>
  );
}

type RoomEvent = {
  version: 1;
  sequence: number | null;
  type: string;
  payload: Record<string, unknown>;
};

function parseRoomEvent(value: unknown): RoomEvent | null {
  try {
    const parsed = JSON.parse(String(value)) as Partial<RoomEvent>;
    if (
      parsed.version !== 1 ||
      typeof parsed.type !== 'string' ||
      !parsed.payload ||
      typeof parsed.payload !== 'object' ||
      (parsed.sequence !== null &&
        parsed.sequence !== undefined &&
        typeof parsed.sequence !== 'number')
    )
      return null;
    return {
      version: 1,
      sequence: parsed.sequence ?? null,
      type: parsed.type,
      payload: parsed.payload,
    };
  } catch {
    return null;
  }
}

function loadPendingDuelGuess(roomId: string): PendingDuelGuess | null {
  try {
    const pending = JSON.parse(
      localStorage.getItem(duelPendingStorageKey(roomId)) ?? 'null',
    ) as Partial<PendingDuelGuess> | null;
    return pending && Array.isArray(pending.guess) && typeof pending.idempotencyKey === 'string'
      ? (pending as PendingDuelGuess)
      : null;
  } catch {
    return null;
  }
}

export function DuelPanel({ roomId }: { roomId: string }) {
  const t = useTranslations('Rooms');
  const tg = useTranslations('Game');
  const tc = useTranslations('Common');
  const api = useApi();
  const analytics = useProductAnalytics();
  const { user } = useSession();
  const router = useRouter();
  const [room, setRoom] = useState<DuelRoom | null>(null);
  const [game, setGame] = useState<Game | null>(null);
  const [row, setRow] = useState<string[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      return JSON.parse(localStorage.getItem(duelRowStorageKey(roomId)) ?? '[]') as string[];
    } catch {
      return [];
    }
  });
  const [connection, setConnection] = useState<'loading' | 'ready' | 'error' | 'empty'>('loading');
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');
  const socketRef = useRef<WebSocket | null>(null);
  const sequenceRef = useRef(0);
  const connectedBeforeRef = useRef(false);
  const completionReportedRef = useRef(false);

  const opponent = useMemo(
    () => room?.members.find((member) => member.userId !== user?.id) ?? null,
    [room, user],
  );

  useEffect(() => {
    let active = true;
    let heartbeat: ReturnType<typeof setInterval> | undefined;
    let reconnect: ReturnType<typeof setTimeout> | undefined;
    const reconcileRoomCompletion = async (gameId: string) => {
      try {
        const [nextGame, nextRoom] = await Promise.all([
          api<Game>(`/v1/games/${encodeURIComponent(gameId)}`),
          api<Room>(`/v1/rooms/${encodeURIComponent(roomId)}`),
        ]);
        if (!active) return;
        setGame(nextGame);
        setRoom({
          ...withReadyMembers(nextRoom),
          roomCode: nextRoom.roomCode ?? tc('private'),
        });
        if (!completionReportedRef.current && nextRoom.status === 'completed') {
          completionReportedRef.current = true;
          analytics('duel_completed', {
            result: nextRoom.isTie ? 'tie' : nextGame.status === 'won' ? 'won' : 'lost',
            attemptsUsed: nextGame.attemptsUsed,
            tie: nextRoom.isTie,
          });
        }
      } catch {
        if (active) setError(t('roomError'));
      }
    };
    const connect = async () => {
      try {
        const initial = await api<Room>(`/v1/rooms/${encodeURIComponent(roomId)}`);
        if (!active) return;
        if (initial.status === 'waiting') {
          router.replace(`/rooms/${roomId}`);
          return;
        }
        const readyInitial = withReadyMembers(initial);
        setRoom({ ...readyInitial, roomCode: initial.roomCode ?? tc('private') });
        const mine = readyInitial.members.find((member) => member.userId === user?.id);
        if (mine?.gameId) {
          const initialGame = await api<Game>(`/v1/games/${encodeURIComponent(mine.gameId)}`);
          if (!active) return;
          setGame(initialGame);
          if (readyInitial.status === 'completed') {
            await reconcileRoomCompletion(mine.gameId);
            if (active) setConnection('ready');
            return;
          }
        }
        if (readyInitial.status === 'expired' || readyInitial.status === 'terminated') {
          setConnection('empty');
          return;
        }
        const { ticket } = await api<{ ticket: string; expiresAt: string }>(
          `/v1/rooms/${encodeURIComponent(roomId)}/ws-ticket`,
          { method: 'POST' },
        );
        if (!active) return;
        const wsOrigin = API_ORIGIN.replace(/^http/, 'ws');
        const socket = new WebSocket(
          `${wsOrigin}/v1/rooms/${encodeURIComponent(roomId)}/events?after=${sequenceRef.current}`,
          ['cipherboard-v1', `ticket.${ticket}`],
        );
        socketRef.current = socket;
        socket.onopen = () => {
          const reconnecting = connectedBeforeRef.current;
          connectedBeforeRef.current = true;
          setConnection('ready');
          analytics('room_joined', {
            roomState: analyticsRoomState(initial.status),
            reconnect: reconnecting,
          });
          if (reconnecting) analytics('reconnect', { surface: 'room', recovered: true });
          heartbeat = setInterval(
            () =>
              socket.readyState === WebSocket.OPEN &&
              socket.send(JSON.stringify({ version: 1, type: 'heartbeat' })),
            20000,
          );
        };
        socket.onmessage = (message) => {
          const event = parseRoomEvent(message.data);
          if (!event) {
            setError(t('protocolError'));
            socket.close(1002, 'Invalid event envelope');
            return;
          }
          if (event.type === 'resync_required') {
            sequenceRef.current = 0;
            socket.close();
            return;
          }
          if (
            event.type !== 'snapshot' &&
            event.sequence !== null &&
            event.sequence <= sequenceRef.current
          )
            return;
          if (event.sequence !== null)
            sequenceRef.current = Math.max(sequenceRef.current, event.sequence);
          if (event.type === 'snapshot') {
            const snapshot = event.payload as unknown as Room;
            setRoom({
              ...withReadyMembers(snapshot),
              roomCode: snapshot.roomCode ?? tc('private'),
            });
          }
          if (event.type === 'presence' || event.type === 'opponent_progress')
            setRoom((current) =>
              current
                ? {
                    ...current,
                    members: current.members.map((member) =>
                      member.userId === event.payload.userId
                        ? {
                            ...member,
                            ...('connected' in event.payload
                              ? { connected: Boolean(event.payload.connected) }
                              : {}),
                            ...('attemptsUsed' in event.payload
                              ? {
                                  attemptsUsed: Number(event.payload.attemptsUsed),
                                  completed: Boolean(event.payload.completed),
                                }
                              : {}),
                          }
                        : member,
                    ),
                  }
                : current,
            );
          if (event.type === 'attempt_result') {
            const attempt: Attempt = {
              number: Number(event.payload.number),
              guess: event.payload.guess as string[],
              feedback: event.payload.feedback as { black: number; white: number },
              submittedAt: new Date().toISOString(),
            };
            setGame((current) =>
              current
                ? {
                    ...current,
                    attempts: [
                      ...current.attempts.filter((item) => item.number !== attempt.number),
                      attempt,
                    ],
                    attemptsUsed: attempt.number,
                    attemptsRemaining: Math.max(0, current.maxAttempts - attempt.number),
                    status: event.payload.status as Game['status'],
                  }
                : current,
            );
            setAnnouncement(
              tg('attemptAnnouncement', {
                number: attempt.number,
                black: attempt.feedback.black,
                white: attempt.feedback.white,
                remaining: Math.max(0, (initial.config.maxAttempts ?? 0) - attempt.number),
              }),
            );
            setRow([]);
            localStorage.removeItem(duelRowStorageKey(roomId));
            localStorage.removeItem(duelPendingStorageKey(roomId));
          }
          if (event.type === 'room_completed' && mine?.gameId)
            void reconcileRoomCompletion(mine.gameId);
          if (event.type === 'error') setError(tg('genericError'));
        };
        socket.onclose = () => {
          if (heartbeat) clearInterval(heartbeat);
          if (active) {
            if (connectedBeforeRef.current)
              analytics('reconnect', { surface: 'room', recovered: false });
            setConnection('loading');
            reconnect = setTimeout(() => void connect(), 1500);
          }
        };
        socket.onerror = () => setConnection('error');
      } catch {
        if (active) setConnection('error');
      }
    };
    if (user) void connect();
    return () => {
      active = false;
      if (heartbeat) clearInterval(heartbeat);
      if (reconnect) clearTimeout(reconnect);
      socketRef.current?.close();
    };
  }, [analytics, api, roomId, router, t, tc, tg, user]);

  useEffect(() => {
    if (row.length) localStorage.setItem(duelRowStorageKey(roomId), JSON.stringify(row));
    else localStorage.removeItem(duelRowStorageKey(roomId));
  }, [roomId, row]);

  const choose = (colour: string) =>
    setRow((current) => [...current, colour].slice(0, room?.config.codeLength ?? 0));
  const submit = () => {
    if (
      !room ||
      row.length !== room.config.codeLength ||
      socketRef.current?.readyState !== WebSocket.OPEN
    )
      return;
    let pending = loadPendingDuelGuess(roomId);
    if (!pending || JSON.stringify(pending.guess) !== JSON.stringify(row))
      pending = { guess: [...row], idempotencyKey: crypto.randomUUID() };
    localStorage.setItem(duelPendingStorageKey(roomId), JSON.stringify(pending));
    setError(null);
    socketRef.current.send(
      JSON.stringify({
        version: 1,
        type: 'guess',
        guess: pending.guess,
        idempotencyKey: pending.idempotencyKey,
      }),
    );
  };

  return (
    <AsyncState
      state={connection}
      loadingLabel={t('reconnecting')}
      errorLabel={t('serviceDown')}
      emptyLabel={t('expired')}
    >
      {room && game ? (
        <div className="duel-layout">
          <header className="game-header">
            <div>
              <p className="mode-label">{t('duelTitle')}</p>
              <h2>{t('roomCode', { code: room.roomCode })}</h2>
            </div>
            <div className="status success">{tc('online')}</div>
          </header>
          <div className="board-layout">
            <section className="attempt-board" aria-label={tg('board')}>
              {game.attempts.length === 0 ? (
                <p className="board-empty">{tg('firstGuess')}</p>
              ) : (
                game.attempts.map((attempt) => (
                  <div
                    className="attempt-row"
                    role="group"
                    aria-label={tg('attemptRow', {
                      number: attempt.number,
                      black: attempt.feedback.black,
                      white: attempt.feedback.white,
                    })}
                    key={attempt.number}
                  >
                    <span className="attempt-number">{attempt.number}</span>
                    <div className="guess-pegs">
                      {attempt.guess.map((colour, index) => (
                        <span
                          key={`${colour}-${index}`}
                          className={`peg peg-${colour}`}
                          role="img"
                          aria-label={tg(`colors.${colour}`)}
                        >
                          {symbols[colour]}
                        </span>
                      ))}
                    </div>
                    <div className="feedback-pegs" aria-hidden="true">
                      <span>{attempt.feedback.black}●</span>
                      <span>{attempt.feedback.white}○</span>
                    </div>
                  </div>
                ))
              )}
              {game.status === 'active' ? (
                <div className="current-row" role="group" aria-label={tg('currentGuess')}>
                  <span className="attempt-number">{game.attemptsUsed + 1}</span>
                  <div className="guess-pegs">
                    {Array.from({ length: room.config.codeLength }, (_, index) => {
                      const colour = row[index];
                      return (
                        <button
                          type="button"
                          key={index}
                          className={`peg slot ${colour ? `peg-${colour}` : ''}`}
                          onClick={() => setRow((current) => current.slice(0, index))}
                          aria-label={colour ? tg(`colors.${colour}`) : tg('empty')}
                        >
                          {colour ? symbols[colour] : index + 1}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : null}
            </section>
            <div className="peg-controls" role="group" aria-label={tg('picker')}>
              {game.status === 'active' ? (
                <>
                  <h3>{tg('picker')}</h3>
                  <div className="palette">
                    {room.config.colours.map((colour) => (
                      <button
                        type="button"
                        key={colour}
                        className={`peg peg-${colour}`}
                        onClick={() => choose(colour)}
                        aria-label={tg(`colors.${colour}`)}
                      >
                        {symbols[colour]}
                      </button>
                    ))}
                  </div>
                  <div className="game-actions">
                    <button className="button secondary" type="button" onClick={() => setRow([])}>
                      {tg('clear')}
                    </button>
                    <button
                      className="button primary"
                      type="button"
                      onClick={submit}
                      disabled={row.length !== room.config.codeLength}
                    >
                      {tg('submit')}
                    </button>
                  </div>
                </>
              ) : (
                <div className="result-panel">
                  <h3>
                    {room.status === 'completed'
                      ? room.isTie
                        ? t('resultTie')
                        : room.winnerId === user?.id
                          ? t('resultWon')
                          : t('resultLost')
                      : tg(`result.${game.status}`)}
                  </h3>
                  <p>
                    {tg('resultSummary', {
                      attempts: game.attemptsUsed,
                      max: game.maxAttempts,
                      score: game.score ?? 0,
                    })}
                  </p>
                  <Link className="button primary" href={`/play/${game.id}/result`}>
                    {tg('viewResult')}
                  </Link>
                </div>
              )}
              {error ? (
                <p className="inline-error" role="alert">
                  {error}
                </p>
              ) : null}
              <section className="opponent-status" aria-live="polite">
                <h3>{t('opponentProgress')}</h3>
                {opponent ? (
                  <>
                    <p>
                      {opponent.displayName === 'Anonymous breaker'
                        ? tc('anonymous')
                        : opponent.displayName}
                    </p>
                    <p>{t('opponentAttempts', { count: opponent.attemptsUsed })}</p>
                    <p>
                      {opponent.completed
                        ? t('opponentComplete')
                        : opponent.connected
                          ? t('connected')
                          : t('disconnected')}
                    </p>
                  </>
                ) : (
                  <p>{t('waiting')}</p>
                )}
                <p className="quiet-note">{t('tieWindow')}</p>
              </section>
            </div>
          </div>
          <div className="sr-only" aria-live="polite">
            {announcement}
          </div>
        </div>
      ) : null}
    </AsyncState>
  );
}
