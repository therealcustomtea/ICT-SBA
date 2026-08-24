// Selects the runtime or strict execution mode for this module.
'use client';

// Imports the dependency used by this module.
import { useTranslations } from 'next-intl';
// Imports the dependency used by this module.
import { useSearchParams } from 'next/navigation';
// Imports the dependency used by this module.
import { useEffect, useMemo, useRef, useState } from 'react';
// Imports the dependency used by this module.
import { AsyncState } from '@/components/feature-page';
// Imports the dependency used by this module.
import { useSession } from '@/components/session-provider';
// Imports the dependency used by this module.
import { Link, useRouter } from '@/i18n/navigation';
// Imports the dependency used by this module.
import { API_ORIGIN, type Attempt, type Game, type Room, useApi } from '@/lib/api';
// Imports the dependency used by this module.
import { useProductAnalytics } from '@/lib/use-product-analytics';

// Declares the RoomMember data shape or implementation.
type RoomMember = {
  // Defines the userId field in the surrounding object or type.
  userId: string;
  // Defines the displayName field in the surrounding object or type.
  displayName: string;
  // Defines the connected field in the surrounding object or type.
  connected: boolean;
  // Defines the ready field in the surrounding object or type.
  ready: boolean;
  // Defines the attemptsUsed field in the surrounding object or type.
  attemptsUsed: number;
  // Defines the completed field in the surrounding object or type.
  completed: boolean;
  // Defines the gameId field in the surrounding object or type.
  gameId: string | null;
  // Closes the expression, call, or declaration started above.
};
// Declares the LobbyRoom data shape or implementation.
type LobbyRoom = Omit<Room, 'members'> & { members: RoomMember[] };
// Declares the DuelRoom data shape or implementation.
type DuelRoom = Omit<LobbyRoom, 'roomCode'> & { roomCode: string };
// Declares the PendingDuelGuess data shape or implementation.
type PendingDuelGuess = { guess: string[]; idempotencyKey: string };
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
// Computes and stores roomInviteStorageKey for subsequent operations.
const roomInviteStorageKey = (roomId: string) => `cipherboard:room-invite:${roomId}`;
// Computes and stores duelRowStorageKey for subsequent operations.
const duelRowStorageKey = (roomId: string) => `cipherboard:duel-row:${roomId}`;
// Computes and stores duelPendingStorageKey for subsequent operations.
const duelPendingStorageKey = (roomId: string) => `cipherboard:duel-pending:${roomId}`;
// Computes and stores analyticsRoomState for subsequent operations.
const analyticsRoomState = (status: string) =>
  // Provides the status value to the surrounding call or element.
  status === 'active' || status === 'completed' || status === 'expired' || status === 'terminated'
    ? // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      status
    : // Continues the surrounding operation with this required value or expression.
      // Executes this line as the next step in the surrounding logic.
      'waiting';
// Computes and stores withReadyMembers for subsequent operations.
const withReadyMembers = (room: Room): LobbyRoom => ({
  // Supplies this item to the surrounding call or collection.
  ...room,
  // Defines the members field in the surrounding object or type.
  members: room.members.map((member) => ({
    // Supplies this item to the surrounding call or collection.
    ...member,
    // Defines the ready field in the surrounding object or type.
    ready: Boolean('ready' in member && member.ready),
    // Closes the expression, call, or declaration started above.
  })),
  // Closes the expression, call, or declaration started above.
});

// Exports this declaration for use by other modules.
export function RoomEntry() {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Rooms');
  // Computes and stores tp for subsequent operations.
  const tp = useTranslations('Play');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Computes and stores analytics for subsequent operations.
  const analytics = useProductAnalytics();
  // Computes and stores router for subsequent operations.
  const router = useRouter();
  // Computes and stores searchParams for subsequent operations.
  const searchParams = useSearchParams();
  // Executes this line as the next step in the surrounding logic.
  const [difficulty, setDifficulty] = useState<'easy' | 'normal' | 'hard' | 'expert'>('normal');
  // Executes this line as the next step in the surrounding logic.
  const [code, setCode] = useState(() => searchParams.get('code') ?? '');
  // Executes this line as the next step in the surrounding logic.
  const [pending, setPending] = useState<'create' | 'join' | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);
  // Computes and stores roomCreationKeyRef for subsequent operations.
  const roomCreationKeyRef = useRef<string | null>(null);

  // Computes and stores create for subsequent operations.
  const create = async () => {
    // Calls setPending with the supplied values.
    setPending('create');
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Executes this line as the next step in the surrounding logic.
      roomCreationKeyRef.current ??= crypto.randomUUID();
      // Computes and stores room for subsequent operations.
      const room = await api<Room>('/v1/rooms', {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Defines the body field in the surrounding object or type.
        body: JSON.stringify({ difficulty, idempotencyKey: roomCreationKeyRef.current }),
        // Closes the expression, call, or declaration started above.
      });
      // Checks this condition before running the nested branch.
      if (!room.roomCode) throw new Error('ROOM_INVITE_MISSING');
      // Calls sessionStorage.setItem with the supplied values.
      sessionStorage.setItem(roomInviteStorageKey(room.id), room.roomCode);
      // Calls analytics with the supplied values.
      analytics('room_joined', { roomState: analyticsRoomState(room.status), reconnect: false });
      // Calls router.push with the supplied values.
      router.push(`/rooms/${room.id}`);
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('roomError'));
      // Calls setPending with the supplied values.
      setPending(null);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };
  // Computes and stores join for subsequent operations.
  const join = async (event: React.FormEvent<HTMLFormElement>) => {
    // Calls event.preventDefault with the supplied values.
    event.preventDefault();
    // Calls setPending with the supplied values.
    setPending('join');
    // Calls setError with the supplied values.
    setError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores room for subsequent operations.
      const room = await api<Room>(`/v1/rooms/${encodeURIComponent(code.trim())}/join`, {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Closes the expression, call, or declaration started above.
      });
      // Calls analytics with the supplied values.
      analytics('room_joined', { roomState: analyticsRoomState(room.status), reconnect: false });
      // Calls router.push with the supplied values.
      router.push(`/rooms/${room.id}`);
      // Handles a failure from the protected operation.
    } catch {
      // Calls setError with the supplied values.
      setError(t('roomError'));
      // Calls setPending with the supplied values.
      setPending(null);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the div interface element or component.
    <div className="room-entry-layout">
      {/* Renders the section interface element or component. */}
      <section className="panel">
        {/* Renders the h2 interface element or component. */}
        <h2>{t('create')}</h2>
        {/* Renders the fieldset interface element or component. */}
        <fieldset className="choice-group">
          {/* Renders the legend interface element or component. */}
          <legend>{tp('difficulty')}</legend>
          {/* Renders the div interface element or component. */}
          <div className="segmented-options">
            {/* Executes this line as the next step in the surrounding logic. */}
            {(['easy', 'normal', 'hard', 'expert'] as const).map((value) => (
              // Renders the label interface element or component.
              <label key={value}>
                {/* Renders the input interface element or component. */}
                <input
                  /* Provides the type value to the surrounding call or element. */
                  type="radio"
                  /* Provides the name value to the surrounding call or element. */
                  name="room-difficulty"
                  /* Provides the checked value to the surrounding call or element. */
                  checked={difficulty === value}
                  /* Provides the onChange value to the surrounding call or element. */
                  onChange={() => {
                    // Calls setDifficulty with the supplied values.
                    setDifficulty(value);
                    // Executes this line as the next step in the surrounding logic.
                    roomCreationKeyRef.current = null;
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
        {/* Renders the button interface element or component. */}
        <button
          /* Provides the type value to the surrounding call or element. */
          type="button"
          /* Provides the className value to the surrounding call or element. */
          className="button primary"
          /* Provides the disabled value to the surrounding call or element. */
          disabled={pending !== null}
          /* Provides the onClick value to the surrounding call or element. */
          onClick={() => void create()}
          /* Closes the expression, call, or declaration started above. */
        >
          {/* Executes this line as the next step in the surrounding logic. */}
          {pending === 'create' ? t('creating') : t('create')}
          {/* Closes the button interface element. */}
        </button>
        {/* Closes the section interface element. */}
      </section>
      {/* Renders the form interface element or component. */}
      <form className="panel" onSubmit={(event) => void join(event)}>
        {/* Renders the h2 interface element or component. */}
        <h2>{t('join')}</h2>
        {/* Renders the label interface element or component. */}
        <label>
          {/* Executes this line as the next step in the surrounding logic. */}
          {t('inviteCode')}
          {/* Renders the input interface element or component. */}
          <input
            /* Provides the name value to the surrounding call or element. */
            name="invite-code"
            /* Provides the autoComplete value to the surrounding call or element. */
            autoComplete="off"
            /* Provides the spellCheck value to the surrounding call or element. */
            spellCheck={false}
            /* Provides the value value to the surrounding call or element. */
            value={code}
            /* Provides the onChange value to the surrounding call or element. */
            onChange={(event) => setCode(event.target.value)}
            /* Executes this line as the next step in the surrounding logic. */
            required
            /* Provides the minLength value to the surrounding call or element. */
            minLength={20}
            /* Provides the maxLength value to the surrounding call or element. */
            maxLength={64}
            /* Provides the pattern value to the surrounding call or element. */
            pattern="[A-Za-z0-9_-]+"
            /* Provides the autoCapitalize value to the surrounding call or element. */
            autoCapitalize="none"
            /* Executes this line as the next step in the surrounding logic. */
            aria-describedby="invite-hint"
            /* Executes this line as the next step in the surrounding logic. */
          />
          {/* Closes the label interface element. */}
        </label>
        {/* Renders the small interface element or component. */}
        <small id="invite-hint">{t('inviteHint')}</small>
        {/* Renders the button interface element or component. */}
        <button className="button secondary" disabled={pending !== null}>
          {/* Executes this line as the next step in the surrounding logic. */}
          {pending === 'join' ? t('joining') : t('join')}
          {/* Closes the button interface element. */}
        </button>
        {/* Closes the form interface element. */}
      </form>
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
      {/* Closes the div interface element. */}
    </div>
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function RoomLobby({ roomId }: { roomId: string }) {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Rooms');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Executes this line as the next step in the surrounding logic.
  const { user } = useSession();
  // Executes this line as the next step in the surrounding logic.
  const [room, setRoom] = useState<LobbyRoom | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [createdRoomCode] = useState<string | null>(
    // Continues the surrounding operation with this required value or expression.
    () =>
      // Supplies this item to the surrounding call or collection.
      typeof window === 'undefined' ? null : sessionStorage.getItem(roomInviteStorageKey(roomId)),
    // Closes the expression, call, or declaration started above.
  );
  // Executes this line as the next step in the surrounding logic.
  const [state, setState] = useState<'loading' | 'error' | 'ready'>('loading');
  // Executes this line as the next step in the surrounding logic.
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');
  // Executes this line as the next step in the surrounding logic.
  const [readyPending, setReadyPending] = useState(false);
  // Executes this line as the next step in the surrounding logic.
  const [readyError, setReadyError] = useState<string | null>(null);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Computes and stores refresh for subsequent operations.
    const refresh = () =>
      // Executes this line as the next step in the surrounding logic.
      api<Room>(`/v1/rooms/${encodeURIComponent(roomId)}`)
        // Begins the nested block or object completed below.
        .then((value) => {
          // Checks this condition before running the nested branch.
          if (active) {
            // Calls setRoom with the supplied values.
            setRoom(withReadyMembers(value));
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
    // Executes this line as the next step in the surrounding logic.
    void refresh();
    // Computes and stores timer for subsequent operations.
    const timer = setInterval(refresh, 3000);
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Calls clearInterval with the supplied values.
      clearInterval(timer);
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [api, roomId]);

  // Computes and stores roomCode for subsequent operations.
  const roomCode = createdRoomCode ?? room?.roomCode ?? null;
  // Computes and stores inviteUrl for subsequent operations.
  const inviteUrl =
    // Executes this line as the next step in the surrounding logic.
    roomCode && typeof window !== 'undefined'
      ? // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        `${window.location.origin}/${window.location.pathname.split('/')[1]}/rooms?code=${roomCode}`
      : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        '';
  // Computes and stores copyInvite for subsequent operations.
  const copyInvite = async () => {
    // Checks this condition before running the nested branch.
    if (!inviteUrl) return;
    // Starts an operation whose expected failures are handled below.
    try {
      // Waits for this asynchronous operation to complete.
      await navigator.clipboard.writeText(inviteUrl);
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
  // Computes and stores markReady for subsequent operations.
  const markReady = async () => {
    // Calls setReadyPending with the supplied values.
    setReadyPending(true);
    // Calls setReadyError with the supplied values.
    setReadyError(null);
    // Starts an operation whose expected failures are handled below.
    try {
      // Computes and stores nextRoom for subsequent operations.
      const nextRoom = await api<Room>(`/v1/rooms/${encodeURIComponent(roomId)}/ready`, {
        // Defines the method field in the surrounding object or type.
        method: 'POST',
        // Closes the expression, call, or declaration started above.
      });
      // Calls setRoom with the supplied values.
      setRoom(withReadyMembers(nextRoom));
      // Handles a failure from the protected operation.
    } catch {
      // Calls setReadyError with the supplied values.
      setReadyError(t('roomError'));
      // Runs cleanup regardless of the protected result.
    } finally {
      // Calls setReadyPending with the supplied values.
      setReadyPending(false);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };
  // Computes and stores currentMember for subsequent operations.
  const currentMember = room?.members.find((member) => member.userId === user?.id) ?? null;
  // Returns this result to the caller and ends the current function.
  return (
    // Renders the AsyncState interface element or component.
    <AsyncState
      /* Provides the state value to the surrounding call or element. */
      state={state}
      /* Provides the loadingLabel value to the surrounding call or element. */
      loadingLabel={tc('loading')}
      /* Provides the errorLabel value to the surrounding call or element. */
      errorLabel={t('roomError')}
      /* Provides the emptyLabel value to the surrounding call or element. */
      emptyLabel={t('expired')}
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Executes this line as the next step in the surrounding logic. */}
      {room ? (
        // Renders the div interface element or component.
        <div className="lobby-layout">
          {/* Renders the section interface element or component. */}
          <section className="panel">
            {/* Executes this line as the next step in the surrounding logic. */}
            {roomCode ? (
              // Starts a JSX fragment that groups the following interface elements.
              <>
                {/* Renders the p interface element or component. */}
                <p className="mode-label">{t('roomCode', { code: roomCode })}</p>
                {/* Renders the h2 interface element or component. */}
                <h2>{t('invite')}</h2>
                {/* Renders the label interface element or component. */}
                <label>
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {t('inviteCode')}
                  {/* Renders the input interface element or component. */}
                  <input
                    /* Provides the name value to the surrounding call or element. */
                    name="invite-url"
                    /* Provides the autoComplete value to the surrounding call or element. */
                    autoComplete="off"
                    /* Provides the spellCheck value to the surrounding call or element. */
                    spellCheck={false}
                    /* Executes this line as the next step in the surrounding logic. */
                    readOnly
                    /* Provides the value value to the surrounding call or element. */
                    value={inviteUrl}
                    /* Executes this line as the next step in the surrounding logic. */
                  />
                  {/* Closes the label interface element. */}
                </label>
                {/* Renders the button interface element or component. */}
                <button
                  /* Provides the className value to the surrounding call or element. */
                  className="button secondary"
                  /* Provides the type value to the surrounding call or element. */
                  type="button"
                  /* Provides the onClick value to the surrounding call or element. */
                  onClick={() => void copyInvite()}
                  /* Closes the expression, call, or declaration started above. */
                >
                  {/* Executes this line as the next step in the surrounding logic. */}
                  {copyState === 'copied' ? tc('copied') : tc('copy')}
                  {/* Closes the button interface element. */}
                </button>
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
                  {copyState === 'copied'
                    ? // Continues the surrounding operation with this required value or expression.
                      // Executes this line as the next step in the surrounding logic.
                      tc('copied')
                    : // Continues the surrounding operation with this required value or expression.
                      // Executes this line as the next step in the surrounding logic.
                      copyState === 'error'
                      ? // Continues the surrounding operation with this required value or expression.
                        // Executes this line as the next step in the surrounding logic.
                        tc('copyError')
                      : // Continues the surrounding operation with this required value or expression.
                        // Executes this line as the next step in the surrounding logic.
                        ''}
                  {/* Closes the p interface element. */}
                </p>
                {/* Closes the JSX fragment started above. */}
              </>
            ) : (
              // Executes this line as the next step in the surrounding logic.
              // Renders the p interface element or component.
              <p className="quiet-note">{t('inviteUnavailable')}</p>
              // Closes the expression, call, or declaration started above.
            )}
            {/* Closes the section interface element. */}
          </section>
          {/* Renders the section interface element or component. */}
          <section className="panel">
            {/* Renders the h2 interface element or component. */}
            <h2>{t('players')}</h2>
            {/* Renders the ul interface element or component. */}
            <ul className="member-list">
              {/* Executes this line as the next step in the surrounding logic. */}
              {room.members.map((member) => (
                // Renders the li interface element or component.
                <li key={member.userId}>
                  {/* Renders the span interface element or component. */}
                  <span>
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {member.displayName === 'Anonymous breaker'
                      ? // Continues the surrounding operation with this required value or expression.
                        // Executes this line as the next step in the surrounding logic.
                        tc('anonymous')
                      : // Continues the surrounding operation with this required value or expression.
                        // Executes this line as the next step in the surrounding logic.
                        member.displayName}
                    {/* Closes the span interface element. */}
                  </span>
                  {/* Renders the span interface element or component. */}
                  <span className="member-state">
                    {/* Renders the span interface element or component. */}
                    <span className={member.ready ? 'status success' : 'status muted'}>
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {member.ready ? t('ready') : t('notReady')}
                      {/* Closes the span interface element. */}
                    </span>
                    {/* Renders the span interface element or component. */}
                    <span className={member.connected ? 'status success' : 'status muted'}>
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {member.connected ? t('connected') : t('disconnected')}
                      {/* Closes the span interface element. */}
                    </span>
                    {/* Closes the span interface element. */}
                  </span>
                  {/* Closes the li interface element. */}
                </li>
                // Closes the expression, call, or declaration started above.
              ))}
              {/* Closes the ul interface element. */}
            </ul>
            {/* Executes this line as the next step in the surrounding logic. */}
            {room.status === 'waiting' ? (
              // Starts a JSX fragment that groups the following interface elements.
              <>
                {/* Renders the p interface element or component. */}
                <p role="status">{room.members.length < 2 ? t('waiting') : t('waitingForReady')}</p>
                {/* Executes this line as the next step in the surrounding logic. */}
                {currentMember && !currentMember.ready ? (
                  // Renders the button interface element or component.
                  <button
                    /* Provides the className value to the surrounding call or element. */
                    className="button primary"
                    /* Provides the type value to the surrounding call or element. */
                    type="button"
                    /* Provides the disabled value to the surrounding call or element. */
                    disabled={readyPending}
                    /* Provides the onClick value to the surrounding call or element. */
                    onClick={() => void markReady()}
                    /* Closes the expression, call, or declaration started above. */
                  >
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {readyPending ? t('markingReady') : t('markReady')}
                    {/* Closes the button interface element. */}
                  </button>
                ) : // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                currentMember?.ready ? (
                  // Renders the p interface element or component.
                  <p className="notice success" role="status">
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {t('youAreReady')}
                    {/* Closes the p interface element. */}
                  </p>
                ) : // Continues the surrounding operation with this required value or expression.
                // Executes this line as the next step in the surrounding logic.
                null}
                {/* Closes the JSX fragment started above. */}
              </>
            ) : (
              // Executes this line as the next step in the surrounding logic.
              // Renders the Link interface element or component.
              <Link className="button primary" href={`/rooms/${room.id}/duel`}>
                {/* Executes this line as the next step in the surrounding logic. */}
                {t('start')}
                {/* Closes the Link interface element. */}
              </Link>
              // Closes the expression, call, or declaration started above.
            )}
            {/* Executes this line as the next step in the surrounding logic. */}
            {readyError ? (
              // Renders the p interface element or component.
              <p className="inline-error" role="alert">
                {/* Executes this line as the next step in the surrounding logic. */}
                {readyError}
                {/* Closes the p interface element. */}
              </p>
            ) : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            null}
            {/* Closes the section interface element. */}
          </section>
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

// Declares the RoomEvent data shape or implementation.
type RoomEvent = {
  // Defines the version field in the surrounding object or type.
  version: 1;
  // Defines the sequence field in the surrounding object or type.
  sequence: number | null;
  // Defines the type field in the surrounding object or type.
  type: string;
  // Defines the payload field in the surrounding object or type.
  payload: Record<string, unknown>;
  // Closes the expression, call, or declaration started above.
};

// Defines the parseRoomEvent function and its callable behavior.
function parseRoomEvent(value: unknown): RoomEvent | null {
  // Starts an operation whose expected failures are handled below.
  try {
    // Computes and stores parsed for subsequent operations.
    const parsed = JSON.parse(String(value)) as Partial<RoomEvent>;
    // Checks this condition before running the nested branch.
    if (
      // Executes this line as the next step in the surrounding logic.
      parsed.version !== 1 ||
      // Executes this line as the next step in the surrounding logic.
      typeof parsed.type !== 'string' ||
      // Executes this line as the next step in the surrounding logic.
      !parsed.payload ||
      // Executes this line as the next step in the surrounding logic.
      typeof parsed.payload !== 'object' ||
      // Executes this line as the next step in the surrounding logic.
      (parsed.sequence !== null &&
        // Executes this line as the next step in the surrounding logic.
        parsed.sequence !== undefined &&
        // Executes this line as the next step in the surrounding logic.
        typeof parsed.sequence !== 'number')
      // Closes the expression, call, or declaration started above.
    )
      // Returns this result to the caller and ends the current function.
      return null;
    // Returns this result to the caller and ends the current function.
    return {
      // Defines the version field in the surrounding object or type.
      version: 1,
      // Defines the sequence field in the surrounding object or type.
      sequence: parsed.sequence ?? null,
      // Defines the type field in the surrounding object or type.
      type: parsed.type,
      // Defines the payload field in the surrounding object or type.
      payload: parsed.payload,
      // Closes the expression, call, or declaration started above.
    };
    // Handles a failure from the protected operation.
  } catch {
    // Returns this result to the caller and ends the current function.
    return null;
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Defines the loadPendingDuelGuess function and its callable behavior.
function loadPendingDuelGuess(roomId: string): PendingDuelGuess | null {
  // Starts an operation whose expected failures are handled below.
  try {
    // Computes and stores pending for subsequent operations.
    const pending = JSON.parse(
      // Calls localStorage.getItem with the supplied values.
      localStorage.getItem(duelPendingStorageKey(roomId)) ?? 'null',
      // Executes this line as the next step in the surrounding logic.
    ) as Partial<PendingDuelGuess> | null;
    // Returns this result to the caller and ends the current function.
    return pending && Array.isArray(pending.guess) && typeof pending.idempotencyKey === 'string'
      ? // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        (pending as PendingDuelGuess)
      : // Continues the surrounding operation with this required value or expression.
        // Executes this line as the next step in the surrounding logic.
        null;
    // Handles a failure from the protected operation.
  } catch {
    // Returns this result to the caller and ends the current function.
    return null;
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function DuelPanel({ roomId }: { roomId: string }) {
  // Computes and stores t for subsequent operations.
  const t = useTranslations('Rooms');
  // Computes and stores tg for subsequent operations.
  const tg = useTranslations('Game');
  // Computes and stores tc for subsequent operations.
  const tc = useTranslations('Common');
  // Computes and stores api for subsequent operations.
  const api = useApi();
  // Computes and stores analytics for subsequent operations.
  const analytics = useProductAnalytics();
  // Executes this line as the next step in the surrounding logic.
  const { user } = useSession();
  // Computes and stores router for subsequent operations.
  const router = useRouter();
  // Keep navigation current without making connection state rerenders restart the socket.
  const routerRef = useRef(router);
  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Keeps the ref synchronized outside render so reconnects use the latest router.
    routerRef.current = router;
    // Supplies this item to the surrounding call or collection.
  }, [router]);
  // Executes this line as the next step in the surrounding logic.
  const [room, setRoom] = useState<DuelRoom | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [game, setGame] = useState<Game | null>(null);
  // Begins the nested block or object completed below.
  const [row, setRow] = useState<string[]>(() => {
    // Checks this condition before running the nested branch.
    if (typeof window === 'undefined') return [];
    // Starts an operation whose expected failures are handled below.
    try {
      // Returns this result to the caller and ends the current function.
      return JSON.parse(localStorage.getItem(duelRowStorageKey(roomId)) ?? '[]') as string[];
      // Handles a failure from the protected operation.
    } catch {
      // Returns this result to the caller and ends the current function.
      return [];
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  });
  // Executes this line as the next step in the surrounding logic.
  const [connection, setConnection] = useState<'loading' | 'ready' | 'error' | 'empty'>('loading');
  // Executes this line as the next step in the surrounding logic.
  const [error, setError] = useState<string | null>(null);
  // Executes this line as the next step in the surrounding logic.
  const [announcement, setAnnouncement] = useState('');
  // Computes and stores socketRef for subsequent operations.
  const socketRef = useRef<WebSocket | null>(null);
  // Computes and stores sequenceRef for subsequent operations.
  const sequenceRef = useRef(0);
  // Computes and stores connectedBeforeRef for subsequent operations.
  const connectedBeforeRef = useRef(false);
  // Computes and stores completionReportedRef for subsequent operations.
  const completionReportedRef = useRef(false);

  // Computes and stores opponent for subsequent operations.
  const opponent = useMemo(
    // Supplies this item to the surrounding call or collection.
    () => room?.members.find((member) => member.userId !== user?.id) ?? null,
    // Supplies this item to the surrounding call or collection.
    [room, user],
    // Closes the expression, call, or declaration started above.
  );

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Computes and stores active for subsequent operations.
    let active = true;
    // Computes and stores heartbeat for subsequent operations.
    let heartbeat: ReturnType<typeof setInterval> | undefined;
    // Computes and stores reconnect for subsequent operations.
    let reconnect: ReturnType<typeof setTimeout> | undefined;
    // Computes and stores reconcileRoomCompletion for subsequent operations.
    const reconcileRoomCompletion = async (gameId: string) => {
      // Starts an operation whose expected failures are handled below.
      try {
        // Executes this line as the next step in the surrounding logic.
        const [nextGame, nextRoom] = await Promise.all([
          // Supplies this item to the surrounding call or collection.
          api<Game>(`/v1/games/${encodeURIComponent(gameId)}`),
          // Supplies this item to the surrounding call or collection.
          api<Room>(`/v1/rooms/${encodeURIComponent(roomId)}`),
          // Closes the expression, call, or declaration started above.
        ]);
        // Checks this condition before running the nested branch.
        if (!active) return;
        // Calls setGame with the supplied values.
        setGame(nextGame);
        // Calls setRoom with the supplied values.
        setRoom({
          // Supplies this item to the surrounding call or collection.
          ...withReadyMembers(nextRoom),
          // Defines the roomCode field in the surrounding object or type.
          roomCode: nextRoom.roomCode ?? tc('private'),
          // Closes the expression, call, or declaration started above.
        });
        // Checks this condition before running the nested branch.
        if (!completionReportedRef.current && nextRoom.status === 'completed') {
          // Executes this line as the next step in the surrounding logic.
          completionReportedRef.current = true;
          // Calls analytics with the supplied values.
          analytics('duel_completed', {
            // Defines the result field in the surrounding object or type.
            result: nextRoom.isTie ? 'tie' : nextGame.status === 'won' ? 'won' : 'lost',
            // Defines the attemptsUsed field in the surrounding object or type.
            attemptsUsed: nextGame.attemptsUsed,
            // Defines the tie field in the surrounding object or type.
            tie: nextRoom.isTie,
            // Closes the expression, call, or declaration started above.
          });
          // Closes the expression, call, or declaration started above.
        }
        // Handles a failure from the protected operation.
      } catch {
        // Checks this condition before running the nested branch.
        if (active) setError(t('roomError'));
        // Closes the expression, call, or declaration started above.
      }
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores connect for subsequent operations.
    const connect = async () => {
      // Starts an operation whose expected failures are handled below.
      try {
        // Computes and stores initial for subsequent operations.
        const initial = await api<Room>(`/v1/rooms/${encodeURIComponent(roomId)}`);
        // Checks this condition before running the nested branch.
        if (!active) return;
        // Checks this condition before running the nested branch.
        if (initial.status === 'waiting') {
          // Calls router.replace with the supplied values.
          routerRef.current.replace(`/rooms/${roomId}`);
          // Returns this result to the caller and ends the current function.
          return;
          // Closes the expression, call, or declaration started above.
        }
        // Computes and stores readyInitial for subsequent operations.
        const readyInitial = withReadyMembers(initial);
        // Calls setRoom with the supplied values.
        setRoom({ ...readyInitial, roomCode: initial.roomCode ?? tc('private') });
        // Computes and stores mine for subsequent operations.
        const mine = readyInitial.members.find((member) => member.userId === user?.id);
        // Checks this condition before running the nested branch.
        if (mine?.gameId) {
          // Computes and stores initialGame for subsequent operations.
          const initialGame = await api<Game>(`/v1/games/${encodeURIComponent(mine.gameId)}`);
          // Checks this condition before running the nested branch.
          if (!active) return;
          // Calls setGame with the supplied values.
          setGame(initialGame);
          // Checks this condition before running the nested branch.
          if (readyInitial.status === 'completed') {
            // Waits for this asynchronous operation to complete.
            await reconcileRoomCompletion(mine.gameId);
            // Checks this condition before running the nested branch.
            if (active) setConnection('ready');
            // Returns this result to the caller and ends the current function.
            return;
            // Closes the expression, call, or declaration started above.
          }
          // Closes the expression, call, or declaration started above.
        }
        // Checks this condition before running the nested branch.
        if (readyInitial.status === 'expired' || readyInitial.status === 'terminated') {
          // Calls setConnection with the supplied values.
          setConnection('empty');
          // Returns this result to the caller and ends the current function.
          return;
          // Closes the expression, call, or declaration started above.
        }
        // Executes this line as the next step in the surrounding logic.
        const { ticket } = await api<{ ticket: string; expiresAt: string }>(
          // Supplies this item to the surrounding call or collection.
          `/v1/rooms/${encodeURIComponent(roomId)}/ws-ticket`,
          // Supplies this item to the surrounding call or collection.
          { method: 'POST' },
          // Closes the expression, call, or declaration started above.
        );
        // Checks this condition before running the nested branch.
        if (!active) return;
        // Computes and stores wsOrigin for subsequent operations.
        const wsOrigin = API_ORIGIN.replace(/^http/, 'ws');
        // Computes and stores socket for subsequent operations.
        const socket = new WebSocket(
          // Supplies this item to the surrounding call or collection.
          `${wsOrigin}/v1/rooms/${encodeURIComponent(roomId)}/events?after=${sequenceRef.current}`,
          // Supplies this item to the surrounding call or collection.
          ['cipherboard-v1', `ticket.${ticket}`],
          // Closes the expression, call, or declaration started above.
        );
        // Executes this line as the next step in the surrounding logic.
        socketRef.current = socket;
        // Begins the nested block or object completed below.
        socket.onopen = () => {
          // Computes and stores reconnecting for subsequent operations.
          const reconnecting = connectedBeforeRef.current;
          // Executes this line as the next step in the surrounding logic.
          connectedBeforeRef.current = true;
          // Calls setConnection with the supplied values.
          setConnection('ready');
          // Calls analytics with the supplied values.
          analytics('room_joined', {
            // Defines the roomState field in the surrounding object or type.
            roomState: analyticsRoomState(initial.status),
            // Defines the reconnect field in the surrounding object or type.
            reconnect: reconnecting,
            // Closes the expression, call, or declaration started above.
          });
          // Checks this condition before running the nested branch.
          if (reconnecting) analytics('reconnect', { surface: 'room', recovered: true });
          // Provides the heartbeat value to the surrounding call or element.
          heartbeat = setInterval(
            // Executes this line as the next step in the surrounding logic.
            () =>
              // Executes this line as the next step in the surrounding logic.
              socket.readyState === WebSocket.OPEN &&
              // Calls socket.send with the supplied values.
              socket.send(JSON.stringify({ version: 1, type: 'heartbeat' })),
            // Supplies this item to the surrounding call or collection.
            20000,
            // Closes the expression, call, or declaration started above.
          );
          // Closes the expression, call, or declaration started above.
        };
        // Begins the nested block or object completed below.
        socket.onmessage = (message) => {
          // Computes and stores event for subsequent operations.
          const event = parseRoomEvent(message.data);
          // Checks this condition before running the nested branch.
          if (!event) {
            // Calls setError with the supplied values.
            setError(t('protocolError'));
            // Calls socket.close with the supplied values.
            socket.close(1002, 'Invalid event envelope');
            // Returns this result to the caller and ends the current function.
            return;
            // Closes the expression, call, or declaration started above.
          }
          // Checks this condition before running the nested branch.
          if (event.type === 'resync_required') {
            // Executes this line as the next step in the surrounding logic.
            sequenceRef.current = 0;
            // Calls socket.close with the supplied values.
            socket.close();
            // Returns this result to the caller and ends the current function.
            return;
            // Closes the expression, call, or declaration started above.
          }
          // Checks this condition before running the nested branch.
          if (
            // Executes this line as the next step in the surrounding logic.
            event.type !== 'snapshot' &&
            // Executes this line as the next step in the surrounding logic.
            event.sequence !== null &&
            // Executes this line as the next step in the surrounding logic.
            event.sequence <= sequenceRef.current
            // Closes the expression, call, or declaration started above.
          )
            // Returns this result to the caller and ends the current function.
            return;
          // Checks this condition before running the nested branch.
          if (event.sequence !== null)
            // Executes this line as the next step in the surrounding logic.
            sequenceRef.current = Math.max(sequenceRef.current, event.sequence);
          // Checks this condition before running the nested branch.
          if (event.type === 'snapshot') {
            // Computes and stores snapshot for subsequent operations.
            const snapshot = event.payload as unknown as Room;
            // Calls setRoom with the supplied values.
            setRoom({
              // Supplies this item to the surrounding call or collection.
              ...withReadyMembers(snapshot),
              // Defines the roomCode field in the surrounding object or type.
              roomCode: snapshot.roomCode ?? tc('private'),
              // Closes the expression, call, or declaration started above.
            });
            // Closes the expression, call, or declaration started above.
          }
          // Checks this condition before running the nested branch.
          if (event.type === 'presence' || event.type === 'opponent_progress')
            // Calls setRoom with the supplied values.
            setRoom(
              // Continues the surrounding operation with this required value or expression.
              (current) =>
                // Executes this line as the next step in the surrounding logic.
                current
                  ? // Continues the surrounding operation with this required value or expression.
                    // Begins the nested block or object completed below.
                    {
                      // Supplies this item to the surrounding call or collection.
                      ...current,
                      // Defines the members field in the surrounding object or type.
                      members: current.members.map(
                        // Continues the surrounding operation with this required value or expression.
                        (member) =>
                          // Executes this line as the next step in the surrounding logic.
                          member.userId === event.payload.userId
                            ? // Continues the surrounding operation with this required value or expression.
                              // Begins the nested block or object completed below.
                              {
                                // Supplies this item to the surrounding call or collection.
                                ...member,
                                // Executes this line as the next step in the surrounding logic.
                                ...('connected' in event.payload
                                  ? // Continues the surrounding operation with this required value or expression.
                                    // Executes this line as the next step in the surrounding logic.
                                    { connected: Boolean(event.payload.connected) }
                                  : // Continues the surrounding operation with this required value or expression.
                                    // Supplies this item to the surrounding call or collection.
                                    {}),
                                // Executes this line as the next step in the surrounding logic.
                                ...('attemptsUsed' in event.payload
                                  ? // Continues the surrounding operation with this required value or expression.
                                    // Begins the nested block or object completed below.
                                    {
                                      // Defines the attemptsUsed field in the surrounding object or type.
                                      attemptsUsed: Number(event.payload.attemptsUsed),
                                      // Defines the completed field in the surrounding object or type.
                                      completed: Boolean(event.payload.completed),
                                      // Closes the expression, call, or declaration started above.
                                    }
                                  : // Continues the surrounding operation with this required value or expression.
                                    // Supplies this item to the surrounding call or collection.
                                    {}),
                                // Closes the expression, call, or declaration started above.
                              }
                            : // Continues the surrounding operation with this required value or expression.
                              // Supplies this item to the surrounding call or collection.
                              member,
                        // Closes the expression, call, or declaration started above.
                      ),
                      // Closes the expression, call, or declaration started above.
                    }
                  : // Continues the surrounding operation with this required value or expression.
                    // Supplies this item to the surrounding call or collection.
                    current,
              // Closes the expression, call, or declaration started above.
            );
          // Checks this condition before running the nested branch.
          if (event.type === 'attempt_result') {
            // Computes and stores attempt for subsequent operations.
            const attempt: Attempt = {
              // Defines the number field in the surrounding object or type.
              number: Number(event.payload.number),
              // Defines the guess field in the surrounding object or type.
              guess: event.payload.guess as string[],
              // Defines the feedback field in the surrounding object or type.
              feedback: event.payload.feedback as { black: number; white: number },
              // Defines the submittedAt field in the surrounding object or type.
              submittedAt: new Date().toISOString(),
              // Closes the expression, call, or declaration started above.
            };
            // Calls setGame with the supplied values.
            setGame(
              // Continues the surrounding operation with this required value or expression.
              (current) =>
                // Executes this line as the next step in the surrounding logic.
                current
                  ? // Continues the surrounding operation with this required value or expression.
                    // Begins the nested block or object completed below.
                    {
                      // Supplies this item to the surrounding call or collection.
                      ...current,
                      // Defines the attempts field in the surrounding object or type.
                      attempts: [
                        // Supplies this item to the surrounding call or collection.
                        ...current.attempts.filter((item) => item.number !== attempt.number),
                        // Supplies this item to the surrounding call or collection.
                        attempt,
                        // Closes the expression, call, or declaration started above.
                      ],
                      // Defines the attemptsUsed field in the surrounding object or type.
                      attemptsUsed: attempt.number,
                      // Defines the attemptsRemaining field in the surrounding object or type.
                      attemptsRemaining: Math.max(0, current.maxAttempts - attempt.number),
                      // Defines the status field in the surrounding object or type.
                      status: event.payload.status as Game['status'],
                      // Closes the expression, call, or declaration started above.
                    }
                  : // Continues the surrounding operation with this required value or expression.
                    // Supplies this item to the surrounding call or collection.
                    current,
              // Closes the expression, call, or declaration started above.
            );
            // Calls setAnnouncement with the supplied values.
            setAnnouncement(
              // Calls tg with the supplied values.
              tg('attemptAnnouncement', {
                // Defines the number field in the surrounding object or type.
                number: attempt.number,
                // Defines the black field in the surrounding object or type.
                black: attempt.feedback.black,
                // Defines the white field in the surrounding object or type.
                white: attempt.feedback.white,
                // Defines the remaining field in the surrounding object or type.
                remaining: Math.max(0, (initial.config.maxAttempts ?? 0) - attempt.number),
                // Closes the expression, call, or declaration started above.
              }),
              // Closes the expression, call, or declaration started above.
            );
            // Calls setRow with the supplied values.
            setRow([]);
            // Calls localStorage.removeItem with the supplied values.
            localStorage.removeItem(duelRowStorageKey(roomId));
            // Calls localStorage.removeItem with the supplied values.
            localStorage.removeItem(duelPendingStorageKey(roomId));
            // Closes the expression, call, or declaration started above.
          }
          // Checks this condition before running the nested branch.
          if (event.type === 'room_completed' && mine?.gameId)
            // Executes this line as the next step in the surrounding logic.
            void reconcileRoomCompletion(mine.gameId);
          // Checks this condition before running the nested branch.
          if (event.type === 'error') setError(tg('genericError'));
          // Closes the expression, call, or declaration started above.
        };
        // Begins the nested block or object completed below.
        socket.onclose = () => {
          // Checks this condition before running the nested branch.
          if (heartbeat) clearInterval(heartbeat);
          // Checks this condition before running the nested branch.
          if (active) {
            // Checks this condition before running the nested branch.
            if (connectedBeforeRef.current)
              // Calls analytics with the supplied values.
              analytics('reconnect', { surface: 'room', recovered: false });
            // Calls setConnection with the supplied values.
            setConnection('loading');
            // Provides the reconnect value to the surrounding call or element.
            reconnect = setTimeout(() => void connect(), 1500);
            // Closes the expression, call, or declaration started above.
          }
          // Closes the expression, call, or declaration started above.
        };
        // Executes this line as the next step in the surrounding logic.
        socket.onerror = () => setConnection('error');
        // Handles a failure from the protected operation.
      } catch {
        // Checks this condition before running the nested branch.
        if (active) setConnection('error');
        // Closes the expression, call, or declaration started above.
      }
      // Closes the expression, call, or declaration started above.
    };
    // Checks this condition before running the nested branch.
    if (user) void connect();
    // Returns this result to the caller and ends the current function.
    return () => {
      // Provides the active value to the surrounding call or element.
      active = false;
      // Checks this condition before running the nested branch.
      if (heartbeat) clearInterval(heartbeat);
      // Checks this condition before running the nested branch.
      if (reconnect) clearTimeout(reconnect);
      // Executes this line as the next step in the surrounding logic.
      socketRef.current?.close();
      // Closes the expression, call, or declaration started above.
    };
    // Executes this line as the next step in the surrounding logic.
  }, [analytics, api, roomId, t, tc, tg, user]);

  // Calls useEffect with the supplied values.
  useEffect(() => {
    // Checks this condition before running the nested branch.
    if (row.length) localStorage.setItem(duelRowStorageKey(roomId), JSON.stringify(row));
    // Executes this line as the next step in the surrounding logic.
    else localStorage.removeItem(duelRowStorageKey(roomId));
    // Executes this line as the next step in the surrounding logic.
  }, [roomId, row]);

  // Computes and stores choose for subsequent operations.
  const choose = (colour: string) =>
    // Calls setRow with the supplied values.
    setRow((current) => [...current, colour].slice(0, room?.config.codeLength ?? 0));
  // Computes and stores submit for subsequent operations.
  const submit = () => {
    // Checks this condition before running the nested branch.
    if (
      // Executes this line as the next step in the surrounding logic.
      !room ||
      // Executes this line as the next step in the surrounding logic.
      row.length !== room.config.codeLength ||
      // Executes this line as the next step in the surrounding logic.
      socketRef.current?.readyState !== WebSocket.OPEN
      // Closes the expression, call, or declaration started above.
    )
      // Returns this result to the caller and ends the current function.
      return;
    // Computes and stores pending for subsequent operations.
    let pending = loadPendingDuelGuess(roomId);
    // Checks this condition before running the nested branch.
    if (!pending || JSON.stringify(pending.guess) !== JSON.stringify(row))
      // Provides the pending value to the surrounding call or element.
      pending = { guess: [...row], idempotencyKey: crypto.randomUUID() };
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem(duelPendingStorageKey(roomId), JSON.stringify(pending));
    // Calls setError with the supplied values.
    setError(null);
    // Calls socketRef.current.send with the supplied values.
    socketRef.current.send(
      // Calls JSON.stringify with the supplied values.
      JSON.stringify({
        // Defines the version field in the surrounding object or type.
        version: 1,
        // Defines the type field in the surrounding object or type.
        type: 'guess',
        // Defines the guess field in the surrounding object or type.
        guess: pending.guess,
        // Defines the idempotencyKey field in the surrounding object or type.
        idempotencyKey: pending.idempotencyKey,
        // Closes the expression, call, or declaration started above.
      }),
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  };

  // Returns this result to the caller and ends the current function.
  return (
    // Renders the AsyncState interface element or component.
    <AsyncState
      /* Provides the state value to the surrounding call or element. */
      state={connection}
      /* Provides the loadingLabel value to the surrounding call or element. */
      loadingLabel={t('reconnecting')}
      /* Provides the errorLabel value to the surrounding call or element. */
      errorLabel={t('serviceDown')}
      /* Provides the emptyLabel value to the surrounding call or element. */
      emptyLabel={t('expired')}
      /* Closes the expression, call, or declaration started above. */
    >
      {/* Executes this line as the next step in the surrounding logic. */}
      {room && game ? (
        // Renders the div interface element or component.
        <div className="duel-layout">
          {/* Renders the header interface element or component. */}
          <header className="game-header">
            {/* Renders the div interface element or component. */}
            <div>
              {/* Renders the p interface element or component. */}
              <p className="mode-label">{t('duelTitle')}</p>
              {/* Renders the h2 interface element or component. */}
              <h2>{t('roomCode', { code: room.roomCode })}</h2>
              {/* Closes the div interface element. */}
            </div>
            {/* Renders the div interface element or component. */}
            <div className="status success">{tc('online')}</div>
            {/* Closes the header interface element. */}
          </header>
          {/* Renders the div interface element or component. */}
          <div className="board-layout">
            {/* Renders the section interface element or component. */}
            <section className="attempt-board" aria-label={tg('board')}>
              {/* Executes this line as the next step in the surrounding logic. */}
              {game.attempts.length === 0 ? (
                // Renders the p interface element or component.
                <p className="board-empty">{tg('firstGuess')}</p>
              ) : (
                // Executes this line as the next step in the surrounding logic.
                // Calls game.attempts.map with the supplied values.
                game.attempts.map((attempt) => (
                  // Renders the div interface element or component.
                  <div
                    /* Provides the className value to the surrounding call or element. */
                    className="attempt-row"
                    /* Provides the role value to the surrounding call or element. */
                    role="group"
                    /* Begins the nested block or object completed below. */
                    aria-label={tg('attemptRow', {
                      // Defines the number field in the surrounding object or type.
                      number: attempt.number,
                      // Defines the black field in the surrounding object or type.
                      black: attempt.feedback.black,
                      // Defines the white field in the surrounding object or type.
                      white: attempt.feedback.white,
                      // Closes the expression, call, or declaration started above.
                    })}
                    /* Provides the key value to the surrounding call or element. */
                    key={attempt.number}
                    /* Closes the expression, call, or declaration started above. */
                  >
                    {/* Renders the span interface element or component. */}
                    <span className="attempt-number">{attempt.number}</span>
                    {/* Renders the div interface element or component. */}
                    <div className="guess-pegs">
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {attempt.guess.map((colour, index) => (
                        // Renders the span interface element or component.
                        <span
                          /* Provides the key value to the surrounding call or element. */
                          key={`${colour}-${index}`}
                          /* Provides the className value to the surrounding call or element. */
                          className={`peg peg-${colour}`}
                          /* Provides the role value to the surrounding call or element. */
                          role="img"
                          /* Executes this line as the next step in the surrounding logic. */
                          aria-label={tg(`colors.${colour}`)}
                          /* Closes the expression, call, or declaration started above. */
                        >
                          {/* Executes this line as the next step in the surrounding logic. */}
                          {symbols[colour]}
                          {/* Closes the span interface element. */}
                        </span>
                        // Closes the expression, call, or declaration started above.
                      ))}
                      {/* Closes the div interface element. */}
                    </div>
                    {/* Renders the div interface element or component. */}
                    <div className="feedback-pegs" aria-hidden="true">
                      {/* Renders the span interface element or component. */}
                      <span>{attempt.feedback.black}●</span>
                      {/* Renders the span interface element or component. */}
                      <span>{attempt.feedback.white}○</span>
                      {/* Closes the div interface element. */}
                    </div>
                    {/* Closes the div interface element. */}
                  </div>
                  // Closes the expression, call, or declaration started above.
                ))
                // Closes the expression, call, or declaration started above.
              )}
              {/* Executes this line as the next step in the surrounding logic. */}
              {game.status === 'active' ? (
                // Renders the div interface element or component.
                <div className="current-row" role="group" aria-label={tg('currentGuess')}>
                  {/* Renders the span interface element or component. */}
                  <span className="attempt-number">{game.attemptsUsed + 1}</span>
                  {/* Renders the div interface element or component. */}
                  <div className="guess-pegs">
                    {/* Begins the nested block or object completed below. */}
                    {Array.from({ length: room.config.codeLength }, (_, index) => {
                      // Computes and stores colour for subsequent operations.
                      const colour = row[index];
                      // Returns this result to the caller and ends the current function.
                      return (
                        // Renders the button interface element or component.
                        <button
                          /* Provides the type value to the surrounding call or element. */
                          type="button"
                          /* Provides the key value to the surrounding call or element. */
                          key={index}
                          /* Provides the className value to the surrounding call or element. */
                          className={`peg slot ${colour ? `peg-${colour}` : ''}`}
                          /* Provides the onClick value to the surrounding call or element. */
                          onClick={() => setRow((current) => current.slice(0, index))}
                          /* Executes this line as the next step in the surrounding logic. */
                          aria-label={colour ? tg(`colors.${colour}`) : tg('empty')}
                          /* Closes the expression, call, or declaration started above. */
                        >
                          {/* Executes this line as the next step in the surrounding logic. */}
                          {colour ? symbols[colour] : index + 1}
                          {/* Closes the button interface element. */}
                        </button>
                        // Closes the expression, call, or declaration started above.
                      );
                      // Closes the expression, call, or declaration started above.
                    })}
                    {/* Closes the div interface element. */}
                  </div>
                  {/* Closes the div interface element. */}
                </div>
              ) : // Continues the surrounding operation with this required value or expression.
              // Executes this line as the next step in the surrounding logic.
              null}
              {/* Closes the section interface element. */}
            </section>
            {/* Renders the div interface element or component. */}
            <div className="peg-controls" role="group" aria-label={tg('picker')}>
              {/* Executes this line as the next step in the surrounding logic. */}
              {game.status === 'active' ? (
                // Starts a JSX fragment that groups the following interface elements.
                <>
                  {/* Renders the h3 interface element or component. */}
                  <h3>{tg('picker')}</h3>
                  {/* Renders the div interface element or component. */}
                  <div className="palette">
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {room.config.colours.map((colour) => (
                      // Renders the button interface element or component.
                      <button
                        /* Provides the type value to the surrounding call or element. */
                        type="button"
                        /* Provides the key value to the surrounding call or element. */
                        key={colour}
                        /* Provides the className value to the surrounding call or element. */
                        className={`peg peg-${colour}`}
                        /* Provides the onClick value to the surrounding call or element. */
                        onClick={() => choose(colour)}
                        /* Executes this line as the next step in the surrounding logic. */
                        aria-label={tg(`colors.${colour}`)}
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
                  {/* Renders the div interface element or component. */}
                  <div className="game-actions">
                    {/* Renders the button interface element or component. */}
                    <button className="button secondary" type="button" onClick={() => setRow([])}>
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {tg('clear')}
                      {/* Closes the button interface element. */}
                    </button>
                    {/* Renders the button interface element or component. */}
                    <button
                      /* Provides the className value to the surrounding call or element. */
                      className="button primary"
                      /* Provides the type value to the surrounding call or element. */
                      type="button"
                      /* Provides the onClick value to the surrounding call or element. */
                      onClick={submit}
                      /* Provides the disabled value to the surrounding call or element. */
                      disabled={row.length !== room.config.codeLength}
                      /* Closes the expression, call, or declaration started above. */
                    >
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {tg('submit')}
                      {/* Closes the button interface element. */}
                    </button>
                    {/* Closes the div interface element. */}
                  </div>
                  {/* Closes the JSX fragment started above. */}
                </>
              ) : (
                // Executes this line as the next step in the surrounding logic.
                // Renders the div interface element or component.
                <div className="result-panel">
                  {/* Renders the h3 interface element or component. */}
                  <h3>
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {room.status === 'completed'
                      ? // Continues the surrounding operation with this required value or expression.
                        // Executes this line as the next step in the surrounding logic.
                        room.isTie
                        ? // Continues the surrounding operation with this required value or expression.
                          // Executes this line as the next step in the surrounding logic.
                          t('resultTie')
                        : // Continues the surrounding operation with this required value or expression.
                          // Executes this line as the next step in the surrounding logic.
                          room.winnerId === user?.id
                          ? // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            t('resultWon')
                          : // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            t('resultLost')
                      : // Continues the surrounding operation with this required value or expression.
                        // Executes this line as the next step in the surrounding logic.
                        tg(`result.${game.status}`)}
                    {/* Closes the h3 interface element. */}
                  </h3>
                  {/* Renders the p interface element or component. */}
                  <p>
                    {/* Begins the nested block or object completed below. */}
                    {tg('resultSummary', {
                      // Defines the attempts field in the surrounding object or type.
                      attempts: game.attemptsUsed,
                      // Defines the max field in the surrounding object or type.
                      max: game.maxAttempts,
                      // Defines the score field in the surrounding object or type.
                      score: game.score ?? 0,
                      // Closes the expression, call, or declaration started above.
                    })}
                    {/* Closes the p interface element. */}
                  </p>
                  {/* Renders the Link interface element or component. */}
                  <Link className="button primary" href={`/play/${game.id}/result`}>
                    {/* Executes this line as the next step in the surrounding logic. */}
                    {tg('viewResult')}
                    {/* Closes the Link interface element. */}
                  </Link>
                  {/* Closes the div interface element. */}
                </div>
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
              {/* Renders the section interface element or component. */}
              <section className="opponent-status" aria-live="polite">
                {/* Renders the h3 interface element or component. */}
                <h3>{t('opponentProgress')}</h3>
                {/* Executes this line as the next step in the surrounding logic. */}
                {opponent ? (
                  // Starts a JSX fragment that groups the following interface elements.
                  <>
                    {/* Renders the p interface element or component. */}
                    <p>
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {opponent.displayName === 'Anonymous breaker'
                        ? // Continues the surrounding operation with this required value or expression.
                          // Executes this line as the next step in the surrounding logic.
                          tc('anonymous')
                        : // Continues the surrounding operation with this required value or expression.
                          // Executes this line as the next step in the surrounding logic.
                          opponent.displayName}
                      {/* Closes the p interface element. */}
                    </p>
                    {/* Renders the p interface element or component. */}
                    <p>{t('opponentAttempts', { count: opponent.attemptsUsed })}</p>
                    {/* Renders the p interface element or component. */}
                    <p>
                      {/* Executes this line as the next step in the surrounding logic. */}
                      {opponent.completed
                        ? // Continues the surrounding operation with this required value or expression.
                          // Executes this line as the next step in the surrounding logic.
                          t('opponentComplete')
                        : // Continues the surrounding operation with this required value or expression.
                          // Executes this line as the next step in the surrounding logic.
                          opponent.connected
                          ? // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            t('connected')
                          : // Continues the surrounding operation with this required value or expression.
                            // Executes this line as the next step in the surrounding logic.
                            t('disconnected')}
                      {/* Closes the p interface element. */}
                    </p>
                    {/* Closes the JSX fragment started above. */}
                  </>
                ) : (
                  // Executes this line as the next step in the surrounding logic.
                  // Renders the p interface element or component.
                  <p>{t('waiting')}</p>
                  // Closes the expression, call, or declaration started above.
                )}
                {/* Renders the p interface element or component. */}
                <p className="quiet-note">{t('tieWindow')}</p>
                {/* Closes the section interface element. */}
              </section>
              {/* Closes the div interface element. */}
            </div>
            {/* Closes the div interface element. */}
          </div>
          {/* Renders the div interface element or component. */}
          <div className="sr-only" aria-live="polite">
            {/* Executes this line as the next step in the surrounding logic. */}
            {announcement}
            {/* Closes the div interface element. */}
          </div>
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
