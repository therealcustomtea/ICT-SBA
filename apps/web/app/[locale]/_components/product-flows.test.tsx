import { NextIntlClientProvider } from 'next-intl';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/en.json';
import { AccountPanel } from './account-panels';
import { ChallengeCreator } from './challenge-panels';
import { AchievementsPanel, ProfilePanel } from './data-panels';
import { DuelPanel, RoomEntry, RoomLobby } from './room-panels';
import { SetupForm } from './setup-form';

const nativeWebSocket = globalThis.WebSocket;

const {
  analyticsMock,
  apiMock,
  pushMock,
  replaceMock,
  searchParamsState,
  signOutMock,
  sessionState,
} = vi.hoisted(() => ({
  analyticsMock: vi.fn(),
  apiMock: vi.fn(),
  pushMock: vi.fn(),
  replaceMock: vi.fn(),
  searchParamsState: { value: '' },
  signOutMock: vi.fn(),
  sessionState: {
    user: { id: 'user-1' },
    isGuest: false,
    getAccessToken: vi.fn(),
    signOut: vi.fn(),
  },
}));

vi.mock('@/lib/api', () => {
  class MockApiError extends Error {
    constructor(
      readonly status: number,
      readonly body: { code: string; message: string; requestId: string },
    ) {
      super(body.message);
    }
  }
  return { API_ORIGIN: 'https://api.example.test', ApiError: MockApiError, useApi: () => apiMock };
});
vi.mock('@/lib/use-product-analytics', () => ({ useProductAnalytics: () => analyticsMock }));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({ ...sessionState, signOut: signOutMock }),
}));
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(searchParamsState.value),
}));
vi.mock('@/i18n/navigation', () => ({
  Link: ({ children, href, ...props }: React.ComponentProps<'a'>) => (
    <a href={String(href)} {...props}>
      {children}
    </a>
  ),
  useRouter: () => ({ push: pushMock, replace: replaceMock }),
  usePathname: () => '/',
}));

const game = {
  id: 'game-1',
  mode: 'pass_and_play',
  difficulty: 'normal',
  status: 'active',
  config: {
    colours: ['R', 'B', 'G', 'Y', 'W', 'K'],
    codeLength: 4,
    maxAttempts: 10,
    duplicatesAllowed: true,
    codeMaker: 'human',
    visibility: 'private',
    ranked: false,
    timeBonusCap: 300,
  },
  attempts: [],
  attemptsUsed: 0,
  maxAttempts: 10,
  attemptsRemaining: 10,
  startedAt: new Date().toISOString(),
  completedAt: null,
  score: null,
  scoreBreakdown: null,
  ranked: false,
};

const verifiedResults = {
  completedCount: 2,
  winRate: 50,
  averageAttempts: 5,
  scoreDistribution: { zero: 1, '1-999': 0, '1000-1499': 1, '1500+': 0 },
  items: [
    {
      rank: 1,
      playerLabel: 'Breaker A1B2C3',
      result: 'won',
      attemptsUsed: 2,
      maxAttempts: 10,
      score: 1420,
      elapsedSeconds: 42,
      completedAt: '2026-07-15T09:30:00Z',
    },
    {
      rank: 2,
      playerLabel: 'Breaker D4E5F6',
      result: 'lost',
      attemptsUsed: 10,
      maxAttempts: 10,
      score: 0,
      elapsedSeconds: 180,
      completedAt: '2026-07-15T09:35:00Z',
    },
  ],
  page: 1,
  pageSize: 10,
  total: 2,
};

const profileStats = {
  gamesPlayed: 4,
  gamesWon: 3,
  gamesLost: 1,
  gamesAbandoned: 0,
  winRate: 75,
  averageAttemptsOnWins: 4,
  bestScoreByDifficulty: { normal: 1310 },
  dailyStreak: 2,
  dailyCompletionHistory: ['2026-07-15', '2026-07-14', '2026-07-10'],
  fastestEligibleSolve: 42,
  totalBlackPegs: 12,
  totalWhitePegs: 8,
  favouriteMode: 'daily',
  achievements: ['daily_debut'],
  achievementProgress: { logic_week: { current: 3, target: 7 } },
};

function renderLocalized(node: React.ReactNode) {
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {node}
    </NextIntlClientProvider>,
  );
}

describe('production product flows', () => {
  afterEach(() => {
    cleanup();
    apiMock.mockReset();
    analyticsMock.mockReset();
    pushMock.mockReset();
    replaceMock.mockReset();
    signOutMock.mockReset();
    searchParamsState.value = '';
    localStorage.clear();
    sessionStorage.clear();
    globalThis.WebSocket = nativeWebSocket;
  });

  it('conceals and clears a confirmed pass-and-play code before handover', async () => {
    apiMock.mockResolvedValue(game);
    const user = userEvent.setup();
    renderLocalized(<SetupForm />);
    await user.click(screen.getByRole('radio', { name: 'Pass-and-play Code Maker' }));
    for (const color of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square'])
      await user.click(screen.getByRole('button', { name: color }));

    const secretGroup = screen
      .getAllByRole('group', { name: 'Secret code' })
      .find((element) => element.classList.contains('secret-row')) as HTMLElement;
    expect(
      within(secretGroup).getByRole('img', { name: 'Secret position 1 filled' }),
    ).toHaveTextContent('●');
    expect(within(secretGroup).queryByRole('img', { name: 'Red circle' })).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Confirm and conceal code' }));

    expect(apiMock).not.toHaveBeenCalled();
    expect(screen.queryAllByRole('group', { name: 'Secret code' })).toHaveLength(0);
    expect(
      screen.getByRole('heading', { name: 'Hand the device to the Code Breaker' }),
    ).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Begin Code Breaker turn' }));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/play/game-1'));
    const request = JSON.parse(String((apiMock.mock.calls[0]?.[1] as RequestInit).body)) as {
      secret: string[];
    };
    expect(request.secret).toEqual(['R', 'B', 'G', 'Y']);
  });

  it('creates a custom challenge idempotently and loads creator-only verified results', async () => {
    const bodies: string[] = [];
    let createCalls = 0;
    apiMock.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === '/v1/challenges/mine?page=1&page_size=20')
        return { items: [], page: 1, pageSize: 20, total: 0 };
      if (path.includes('/results')) return verifiedResults;
      if (path === '/v1/challenges' && options?.method === 'POST') {
        bodies.push(String(options.body));
        createCalls += 1;
        if (createCalls === 1) throw new Error('response interrupted');
        return {
          id: 'challenge-1',
          shareCode: 'private-code',
          title: null,
          creatorName: null,
          config: game.config,
          expiresAt: new Date().toISOString(),
          revoked: false,
          completedCount: 3,
        };
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    const user = userEvent.setup();
    renderLocalized(<ChallengeCreator />);
    await user.click(screen.getByRole('radio', { name: 'Custom' }));
    await user.click(screen.getByRole('button', { name: 'Create challenge' }));
    await screen.findByRole('alert');
    await user.click(screen.getByRole('button', { name: 'Create challenge' }));

    expect(await screen.findByRole('heading', { name: 'Verified results' })).toBeVisible();
    const resultBoard = screen.getByRole('table', { name: 'Verified results' });
    expect(
      screen.getByRole('region', { name: 'Scrollable verified results table' }),
    ).toContainElement(resultBoard);
    expect(
      within(resultBoard).getByRole('row', { name: /1 Breaker A1B2C3 won 1,420/ }),
    ).toHaveTextContent('2 of 10');
    const [first, second] = bodies.map(
      (body) =>
        JSON.parse(body) as {
          idempotencyKey: string;
          config: { codeLength: number; ranked: boolean };
        },
    );
    expect(second?.idempotencyKey).toBe(first?.idempotencyKey);
    expect(first?.config).toMatchObject({ codeLength: 4, ranked: false });
    expect(apiMock).toHaveBeenCalledWith('/v1/challenges/challenge-1/results?page=1&page_size=10');
  });

  it('manages returning challenges without reconstructing private share links', async () => {
    const owned = {
      id: 'challenge-2',
      title: 'Returning puzzle',
      showCreatorName: true,
      config: game.config,
      revoked: false,
      expiresAt: new Date(Date.now() + 86_400_000).toISOString(),
      completedCount: 2,
      createdAt: new Date().toISOString(),
    };
    apiMock.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === '/v1/challenges/mine?page=1&page_size=20')
        return { items: [owned], page: 1, pageSize: 20, total: 1 };
      if (path.endsWith('/results?page=1&page_size=10')) return verifiedResults;
      if (path === '/v1/challenges/challenge-2' && options?.method === 'DELETE') return undefined;
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const user = userEvent.setup();
    renderLocalized(<ChallengeCreator />);

    expect(await screen.findByRole('heading', { name: 'Returning puzzle' })).toBeVisible();
    expect(screen.queryByDisplayValue(/challenge/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'View results' }));
    expect(await screen.findByText('50%')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Revoke challenge' }));

    expect(await screen.findByText('Revoked')).toBeVisible();
    expect(apiMock).toHaveBeenCalledWith('/v1/challenges/challenge-2', { method: 'DELETE' });
  });

  it('renders authoritative daily history and progressive achievement data on the profile', async () => {
    apiMock.mockImplementation(async (path: string) => {
      if (path === '/v1/me/profile')
        return {
          id: 'user-1',
          displayName: 'Ada',
          isAnonymous: false,
          publicLeaderboards: true,
          createdAt: '2026-07-01T00:00:00Z',
        };
      if (path === '/v1/me/stats') return profileStats;
      if (path === '/v1/me/games?page=1&page_size=8')
        return { items: [], page: 1, pageSize: 8, total: 0 };
      throw new Error(`Unexpected request: ${path}`);
    });

    renderLocalized(<ProfilePanel />);

    expect(await screen.findByRole('heading', { name: 'Daily challenge history' })).toBeVisible();
    expect(document.querySelector('time[datetime="2026-07-15"]')).toHaveTextContent('Jul 15, 2026');
    expect(screen.getByRole('progressbar', { name: 'Logic Week: 3 of 7' })).toHaveAttribute(
      'value',
      '3',
    );
    expect(screen.getByRole('link', { name: /View all achievements/ })).toHaveAttribute(
      'href',
      '/achievements',
    );
  });

  it('shows server-calculated Logic Week progress in the achievement record', async () => {
    apiMock.mockResolvedValue(profileStats);

    renderLocalized(<AchievementsPanel />);

    expect(await screen.findByRole('heading', { name: 'Logic Week' })).toBeVisible();
    expect(screen.getByText('3 of 7')).toBeVisible();
    expect(screen.getByRole('progressbar', { name: 'Logic Week: 3 of 7' })).toHaveAttribute(
      'max',
      '7',
    );
  });

  it('shows both lobby readiness states and confirms the current player through the ready endpoint', async () => {
    const waitingRoom = {
      id: 'room-1',
      roomCode: 'ABC123',
      status: 'waiting',
      config: game.config,
      members: [
        {
          userId: 'user-1',
          displayName: 'Ada',
          connected: true,
          ready: false,
          attemptsUsed: 0,
          completed: false,
          gameId: 'game-1',
        },
        {
          userId: 'user-2',
          displayName: 'Lin',
          connected: true,
          ready: true,
          attemptsUsed: 0,
          completed: false,
          gameId: null,
        },
      ],
      winnerId: null,
      isTie: false,
      expiresAt: new Date().toISOString(),
      eventSequence: 0,
    };
    apiMock.mockImplementation(async (path: string, options?: RequestInit) =>
      options?.method === 'POST' && path.endsWith('/ready')
        ? {
            ...waitingRoom,
            members: waitingRoom.members.map((member) =>
              member.userId === 'user-1' ? { ...member, ready: true } : member,
            ),
          }
        : waitingRoom,
    );
    const user = userEvent.setup();
    renderLocalized(<RoomLobby roomId="room-1" />);

    expect((await screen.findAllByText('Ready')).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Not ready')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'I’m ready' }));
    expect(await screen.findByText('You’re ready. Waiting for the other player.')).toBeVisible();
    expect(apiMock).toHaveBeenCalledWith('/v1/rooms/room-1/ready', { method: 'POST' });
  });

  it('preserves a mixed-case base64url room invite byte-for-byte when joining', async () => {
    const invite = 'AbCd_ef-GhIjKlMnOpQrStUvWxYz0123456789';
    searchParamsState.value = `code=${invite}`;
    apiMock.mockResolvedValue({ id: 'room-1', status: 'waiting', members: [] });
    const user = userEvent.setup();
    renderLocalized(<RoomEntry />);

    const input = screen.getByRole('textbox', { name: 'Invite code' });
    expect(input).toHaveValue(invite);
    expect(input).toHaveAttribute('autocapitalize', 'none');
    await user.click(screen.getByRole('button', { name: 'Join room' }));

    expect(apiMock).toHaveBeenCalledWith(`/v1/rooms/${invite}/join`, { method: 'POST' });
    expect(pushMock).toHaveBeenCalledWith('/rooms/room-1');
  });

  it('sends explicit deletion confirmation and directs recent-auth failures to sign-in', async () => {
    const { ApiError } = await import('@/lib/api');
    apiMock.mockRejectedValue(
      new ApiError(401, {
        code: 'RECENT_AUTH_REQUIRED',
        message: 'Sign in again',
        requestId: 'request-1',
      }),
    );
    const user = userEvent.setup();
    renderLocalized(<AccountPanel />);
    await user.type(screen.getByRole('textbox', { name: 'Type DELETE to confirm' }), 'DELETE');
    await user.click(screen.getByRole('button', { name: 'Permanently delete account' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'For your protection, sign in again before deleting this account.',
    );
    expect(screen.getByRole('link', { name: 'Sign in again' })).toHaveAttribute('href', '/auth');
    expect(apiMock).toHaveBeenCalledWith('/v1/me', {
      method: 'DELETE',
      body: JSON.stringify({ confirmation: 'DELETE' }),
    });
    expect(signOutMock).not.toHaveBeenCalled();
  });

  it('keeps websocket tickets out of URLs and rejects malformed realtime envelopes', async () => {
    class FakeWebSocket {
      static OPEN = 1;
      static latest: FakeWebSocket | null = null;
      readyState = 0;
      onopen: (() => void) | null = null;
      onmessage: ((message: MessageEvent) => void) | null = null;
      onclose: (() => void) | null = null;
      onerror: (() => void) | null = null;
      send = vi.fn();
      close = vi.fn();
      constructor(
        readonly url: string,
        readonly protocols: string[],
      ) {
        FakeWebSocket.latest = this;
      }
    }
    globalThis.WebSocket = FakeWebSocket as unknown as typeof WebSocket;
    const activeRoom = {
      id: 'room-1',
      roomCode: null,
      status: 'active',
      config: game.config,
      members: [
        {
          userId: 'user-1',
          displayName: 'Ada',
          connected: true,
          ready: true,
          attemptsUsed: 0,
          completed: false,
          gameId: 'game-1',
        },
        {
          userId: 'user-2',
          displayName: 'Lin',
          connected: true,
          ready: true,
          attemptsUsed: 0,
          completed: false,
          gameId: null,
        },
      ],
      winnerId: null,
      isTie: false,
      expiresAt: new Date().toISOString(),
      eventSequence: 0,
    };
    let currentRoom = activeRoom;
    let currentGame = { ...game, mode: 'duel' };
    apiMock.mockImplementation(async (path: string) =>
      path.endsWith('/ws-ticket')
        ? { ticket: 'private_ticket', expiresAt: new Date().toISOString() }
        : path.startsWith('/v1/games/')
          ? currentGame
          : currentRoom,
    );
    renderLocalized(<DuelPanel roomId="room-1" />);
    await waitFor(() => expect(FakeWebSocket.latest).not.toBeNull());
    const connectedSocket = FakeWebSocket.latest;
    expect(connectedSocket?.url).toBe('wss://api.example.test/v1/rooms/room-1/events?after=0');
    expect(connectedSocket?.protocols).toEqual(['cipherboard-v1', 'ticket.private_ticket']);
    if (!connectedSocket) throw new Error('socket not created');
    connectedSocket.readyState = FakeWebSocket.OPEN;
    fireEvent(window, new Event('focus'));
    connectedSocket.onopen?.();
    await screen.findByText('Opponent progress');
    connectedSocket.onmessage?.({
      data: JSON.stringify({
        version: 1,
        sequence: 5,
        type: 'snapshot',
        payload: {
          ...activeRoom,
          eventSequence: 5,
          members: activeRoom.members.map((member) =>
            member.userId === 'user-2' ? { ...member, attemptsUsed: 3 } : member,
          ),
        },
      }),
    } as MessageEvent);
    connectedSocket.onmessage?.({
      data: JSON.stringify({
        version: 1,
        sequence: 4,
        type: 'opponent_progress',
        payload: { userId: 'user-2', attemptsUsed: 1, completed: false },
      }),
    } as MessageEvent);
    expect(await screen.findByText('Opponent attempts: 3')).toBeVisible();

    connectedSocket.onmessage?.({
      data: JSON.stringify({
        version: 1,
        sequence: 6,
        type: 'attempt_result',
        payload: {
          number: 1,
          guess: ['R', 'B', 'G', 'Y'],
          feedback: { black: 4, white: 0 },
          status: 'won',
        },
      }),
    } as MessageEvent);
    await screen.findByText('Code broken');
    expect(analyticsMock).not.toHaveBeenCalledWith('duel_completed', expect.anything());

    currentRoom = {
      ...activeRoom,
      status: 'completed',
      winnerId: null,
      isTie: true,
      eventSequence: 7,
    };
    currentGame = {
      ...currentGame,
      status: 'won',
      attemptsUsed: 1,
      attemptsRemaining: 9,
    };
    const completedEvent = {
      data: JSON.stringify({
        version: 1,
        sequence: 7,
        type: 'room_completed',
        payload: { winnerId: null, isTie: true, reason: 'tie_window' },
      }),
    } as MessageEvent;
    connectedSocket.onmessage?.(completedEvent);
    expect(await screen.findByText('The duel ended in a tie')).toBeVisible();
    connectedSocket.onmessage?.(completedEvent);
    await waitFor(() =>
      expect(analyticsMock.mock.calls.filter(([name]) => name === 'duel_completed')).toHaveLength(
        1,
      ),
    );
    connectedSocket.onmessage?.({ data: '{malformed' } as MessageEvent);
    expect(await screen.findByRole('alert')).toHaveTextContent('The live room protocol changed.');
    expect(connectedSocket.close).toHaveBeenCalledWith(1002, 'Invalid event envelope');
  });
});
