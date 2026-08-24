// Imports the dependency used by this module.
import { NextIntlClientProvider } from 'next-intl';
// Imports the dependency used by this module.
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
// Imports the dependency used by this module.
import userEvent from '@testing-library/user-event';
// Imports the dependency used by this module.
import { afterEach, describe, expect, it, vi } from 'vitest';
// Imports the dependency used by this module.
import messages from '@/messages/en.json';
// Imports the dependency used by this module.
import { AccountPanel } from './account-panels';
// Imports the dependency used by this module.
import { ChallengeCreator } from './challenge-panels';
// Imports the dependency used by this module.
import { AchievementsPanel, ProfilePanel } from './data-panels';
// Imports the dependency used by this module.
import { DuelPanel, RoomEntry, RoomLobby } from './room-panels';
// Imports the dependency used by this module.
import { SetupForm } from './setup-form';

// Computes and stores nativeWebSocket for subsequent operations.
const nativeWebSocket = globalThis.WebSocket;

// Begins the nested block or object completed below.
const {
  // Supplies this item to the surrounding call or collection.
  analyticsMock,
  // Supplies this item to the surrounding call or collection.
  apiMock,
  // Supplies this item to the surrounding call or collection.
  pushMock,
  // Supplies this item to the surrounding call or collection.
  replaceMock,
  // Supplies this item to the surrounding call or collection.
  searchParamsState,
  // Supplies this item to the surrounding call or collection.
  signOutMock,
  // Supplies this item to the surrounding call or collection.
  sessionState,
  // Begins the nested block or object completed below.
} = vi.hoisted(() => ({
  // Defines the analyticsMock field in the surrounding object or type.
  analyticsMock: vi.fn(),
  // Defines the apiMock field in the surrounding object or type.
  apiMock: vi.fn(),
  // Defines the pushMock field in the surrounding object or type.
  pushMock: vi.fn(),
  // Defines the replaceMock field in the surrounding object or type.
  replaceMock: vi.fn(),
  // Defines the searchParamsState field in the surrounding object or type.
  searchParamsState: { value: '' },
  // Defines the signOutMock field in the surrounding object or type.
  signOutMock: vi.fn(),
  // Defines the sessionState field in the surrounding object or type.
  sessionState: {
    // Defines the user field in the surrounding object or type.
    user: { id: 'user-1' },
    // Defines the isGuest field in the surrounding object or type.
    isGuest: false,
    // Defines the getAccessToken field in the surrounding object or type.
    getAccessToken: vi.fn(),
    // Defines the signOut field in the surrounding object or type.
    signOut: vi.fn(),
    // Closes the expression, call, or declaration started above.
  },
  // Closes the expression, call, or declaration started above.
}));

// Calls vi.mock with the supplied values.
vi.mock('@/lib/api', () => {
  // Declares the MockApiError data shape or implementation.
  class MockApiError extends Error {
    // Calls constructor with the supplied values.
    constructor(
      // Supplies this item to the surrounding call or collection.
      readonly status: number,
      // Supplies this item to the surrounding call or collection.
      readonly body: { code: string; message: string; requestId: string },
      // Begins the nested block or object completed below.
    ) {
      // Calls super with the supplied values.
      super(body.message);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  }
  // Returns this result to the caller and ends the current function.
  return { API_ORIGIN: 'https://api.example.test', ApiError: MockApiError, useApi: () => apiMock };
  // Closes the expression, call, or declaration started above.
});
// Calls vi.mock with the supplied values.
vi.mock('@/lib/use-product-analytics', () => ({ useProductAnalytics: () => analyticsMock }));
// Calls vi.mock with the supplied values.
vi.mock('@/components/session-provider', () => ({
  // Defines the useSession field in the surrounding object or type.
  useSession: () => ({ ...sessionState, signOut: signOutMock }),
  // Closes the expression, call, or declaration started above.
}));
// Calls vi.mock with the supplied values.
vi.mock('next/navigation', () => ({
  // Defines the useSearchParams field in the surrounding object or type.
  useSearchParams: () => new URLSearchParams(searchParamsState.value),
  // Closes the expression, call, or declaration started above.
}));
// Calls vi.mock with the supplied values.
vi.mock('@/i18n/navigation', () => ({
  // Defines the Link field in the surrounding object or type.
  Link: ({ children, href, ...props }: React.ComponentProps<'a'>) => (
    // Renders the a interface element or component.
    <a href={String(href)} {...props}>
      {/* Executes this line as the next step in the surrounding logic. */}
      {children}
      {/* Closes the a interface element. */}
    </a>
    // Closes the expression, call, or declaration started above.
  ),
  // Defines the useRouter field in the surrounding object or type.
  useRouter: () => ({ push: pushMock, replace: replaceMock }),
  // Defines the usePathname field in the surrounding object or type.
  usePathname: () => '/',
  // Closes the expression, call, or declaration started above.
}));

// Computes and stores game for subsequent operations.
const game = {
  // Defines the id field in the surrounding object or type.
  id: 'game-1',
  // Defines the mode field in the surrounding object or type.
  mode: 'pass_and_play',
  // Defines the difficulty field in the surrounding object or type.
  difficulty: 'normal',
  // Defines the status field in the surrounding object or type.
  status: 'active',
  // Defines the config field in the surrounding object or type.
  config: {
    // Defines the colours field in the surrounding object or type.
    colours: ['R', 'B', 'G', 'Y', 'W', 'K'],
    // Defines the codeLength field in the surrounding object or type.
    codeLength: 4,
    // Defines the maxAttempts field in the surrounding object or type.
    maxAttempts: 10,
    // Defines the duplicatesAllowed field in the surrounding object or type.
    duplicatesAllowed: true,
    // Defines the codeMaker field in the surrounding object or type.
    codeMaker: 'human',
    // Defines the visibility field in the surrounding object or type.
    visibility: 'private',
    // Defines the ranked field in the surrounding object or type.
    ranked: false,
    // Defines the timeBonusCap field in the surrounding object or type.
    timeBonusCap: 300,
    // Closes the expression, call, or declaration started above.
  },
  // Defines the attempts field in the surrounding object or type.
  attempts: [],
  // Defines the attemptsUsed field in the surrounding object or type.
  attemptsUsed: 0,
  // Defines the maxAttempts field in the surrounding object or type.
  maxAttempts: 10,
  // Defines the attemptsRemaining field in the surrounding object or type.
  attemptsRemaining: 10,
  // Defines the startedAt field in the surrounding object or type.
  startedAt: new Date().toISOString(),
  // Defines the completedAt field in the surrounding object or type.
  completedAt: null,
  // Defines the score field in the surrounding object or type.
  score: null,
  // Defines the scoreBreakdown field in the surrounding object or type.
  scoreBreakdown: null,
  // Defines the ranked field in the surrounding object or type.
  ranked: false,
  // Closes the expression, call, or declaration started above.
};

// Computes and stores verifiedResults for subsequent operations.
const verifiedResults = {
  // Defines the completedCount field in the surrounding object or type.
  completedCount: 2,
  // Defines the winRate field in the surrounding object or type.
  winRate: 50,
  // Defines the averageAttempts field in the surrounding object or type.
  averageAttempts: 5,
  // Defines the scoreDistribution field in the surrounding object or type.
  scoreDistribution: { zero: 1, '1-999': 0, '1000-1499': 1, '1500+': 0 },
  // Defines the items field in the surrounding object or type.
  items: [
    // Begins the nested block or object completed below.
    {
      // Defines the rank field in the surrounding object or type.
      rank: 1,
      // Defines the playerLabel field in the surrounding object or type.
      playerLabel: 'Breaker A1B2C3',
      // Defines the result field in the surrounding object or type.
      result: 'won',
      // Defines the attemptsUsed field in the surrounding object or type.
      attemptsUsed: 2,
      // Defines the maxAttempts field in the surrounding object or type.
      maxAttempts: 10,
      // Defines the score field in the surrounding object or type.
      score: 1420,
      // Defines the elapsedSeconds field in the surrounding object or type.
      elapsedSeconds: 42,
      // Defines the completedAt field in the surrounding object or type.
      completedAt: '2026-07-15T09:30:00Z',
      // Closes the expression, call, or declaration started above.
    },
    // Begins the nested block or object completed below.
    {
      // Defines the rank field in the surrounding object or type.
      rank: 2,
      // Defines the playerLabel field in the surrounding object or type.
      playerLabel: 'Breaker D4E5F6',
      // Defines the result field in the surrounding object or type.
      result: 'lost',
      // Defines the attemptsUsed field in the surrounding object or type.
      attemptsUsed: 10,
      // Defines the maxAttempts field in the surrounding object or type.
      maxAttempts: 10,
      // Defines the score field in the surrounding object or type.
      score: 0,
      // Defines the elapsedSeconds field in the surrounding object or type.
      elapsedSeconds: 180,
      // Defines the completedAt field in the surrounding object or type.
      completedAt: '2026-07-15T09:35:00Z',
      // Closes the expression, call, or declaration started above.
    },
    // Closes the expression, call, or declaration started above.
  ],
  // Defines the page field in the surrounding object or type.
  page: 1,
  // Defines the pageSize field in the surrounding object or type.
  pageSize: 10,
  // Defines the total field in the surrounding object or type.
  total: 2,
  // Closes the expression, call, or declaration started above.
};

// Computes and stores profileStats for subsequent operations.
const profileStats = {
  // Defines the gamesPlayed field in the surrounding object or type.
  gamesPlayed: 4,
  // Defines the gamesWon field in the surrounding object or type.
  gamesWon: 3,
  // Defines the gamesLost field in the surrounding object or type.
  gamesLost: 1,
  // Defines the gamesAbandoned field in the surrounding object or type.
  gamesAbandoned: 0,
  // Defines the winRate field in the surrounding object or type.
  winRate: 75,
  // Defines the averageAttemptsOnWins field in the surrounding object or type.
  averageAttemptsOnWins: 4,
  // Defines the bestScoreByDifficulty field in the surrounding object or type.
  bestScoreByDifficulty: { normal: 1310 },
  // Defines the dailyStreak field in the surrounding object or type.
  dailyStreak: 2,
  // Defines the dailyCompletionHistory field in the surrounding object or type.
  dailyCompletionHistory: ['2026-07-15', '2026-07-14', '2026-07-10'],
  // Defines the fastestEligibleSolve field in the surrounding object or type.
  fastestEligibleSolve: 42,
  // Defines the totalBlackPegs field in the surrounding object or type.
  totalBlackPegs: 12,
  // Defines the totalWhitePegs field in the surrounding object or type.
  totalWhitePegs: 8,
  // Defines the favouriteMode field in the surrounding object or type.
  favouriteMode: 'daily',
  // Defines the achievements field in the surrounding object or type.
  achievements: ['daily_debut'],
  // Defines the achievementProgress field in the surrounding object or type.
  achievementProgress: { logic_week: { current: 3, target: 7 } },
  // Closes the expression, call, or declaration started above.
};

// Defines the renderLocalized function and its callable behavior.
function renderLocalized(node: React.ReactNode) {
  // Returns this result to the caller and ends the current function.
  return render(
    // Renders the NextIntlClientProvider interface element or component.
    <NextIntlClientProvider locale="en" messages={messages}>
      {/* Executes this line as the next step in the surrounding logic. */}
      {node}
      {/* Closes the NextIntlClientProvider interface element. */}
    </NextIntlClientProvider>,
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Calls describe with the supplied values.
describe('production product flows', () => {
  // Calls afterEach with the supplied values.
  afterEach(() => {
    // Calls cleanup with the supplied values.
    cleanup();
    // Calls apiMock.mockReset with the supplied values.
    apiMock.mockReset();
    // Calls analyticsMock.mockReset with the supplied values.
    analyticsMock.mockReset();
    // Calls pushMock.mockReset with the supplied values.
    pushMock.mockReset();
    // Calls replaceMock.mockReset with the supplied values.
    replaceMock.mockReset();
    // Calls signOutMock.mockReset with the supplied values.
    signOutMock.mockReset();
    // Executes this line as the next step in the surrounding logic.
    searchParamsState.value = '';
    // Calls localStorage.clear with the supplied values.
    localStorage.clear();
    // Calls sessionStorage.clear with the supplied values.
    sessionStorage.clear();
    // Executes this line as the next step in the surrounding logic.
    globalThis.WebSocket = nativeWebSocket;
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('conceals and clears a confirmed pass-and-play code before handover', async () => {
    // Calls apiMock.mockResolvedValue with the supplied values.
    apiMock.mockResolvedValue(game);
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderLocalized with the supplied values.
    renderLocalized(<SetupForm />);
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('radio', { name: 'Pass-and-play Code Maker' }));
    // Iterates through these values for the nested operation.
    for (const color of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square'])
      // Waits for this asynchronous operation to complete.
      await user.click(screen.getByRole('button', { name: color }));

    // Computes and stores secretGroup for subsequent operations.
    const secretGroup = screen
      // Executes this line as the next step in the surrounding logic.
      .getAllByRole('group', { name: 'Secret code' })
      // Executes this line as the next step in the surrounding logic.
      .find((element) => element.classList.contains('secret-row')) as HTMLElement;
    // Calls expect with the supplied values.
    expect(
      // Calls within with the supplied values.
      within(secretGroup).getByRole('img', { name: 'Secret position 1 filled' }),
      // Executes this line as the next step in the surrounding logic.
    ).toHaveTextContent('●');
    // Calls expect with the supplied values.
    expect(within(secretGroup).queryByRole('img', { name: 'Red circle' })).not.toBeInTheDocument();
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Confirm and conceal code' }));

    // Calls expect with the supplied values.
    expect(apiMock).not.toHaveBeenCalled();
    // Calls expect with the supplied values.
    expect(screen.queryAllByRole('group', { name: 'Secret code' })).toHaveLength(0);
    // Calls expect with the supplied values.
    expect(
      // Calls screen.getByRole with the supplied values.
      screen.getByRole('heading', { name: 'Hand the device to the Code Breaker' }),
      // Executes this line as the next step in the surrounding logic.
    ).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Begin Code Breaker turn' }));

    // Waits for this asynchronous operation to complete.
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/play/game-1'));
    // Computes and stores request for subsequent operations.
    const request = JSON.parse(String((apiMock.mock.calls[0]?.[1] as RequestInit).body)) as {
      // Defines the secret field in the surrounding object or type.
      secret: string[];
      // Closes the expression, call, or declaration started above.
    };
    // Calls expect with the supplied values.
    expect(request.secret).toEqual(['R', 'B', 'G', 'Y']);
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('creates a custom challenge idempotently and loads creator-only verified results', async () => {
    // Computes and stores bodies for subsequent operations.
    const bodies: string[] = [];
    // Computes and stores createCalls for subsequent operations.
    let createCalls = 0;
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string, options?: RequestInit) => {
      // Checks this condition before running the nested branch.
      if (path === '/v1/challenges/mine?page=1&page_size=20')
        // Returns this result to the caller and ends the current function.
        return { items: [], page: 1, pageSize: 20, total: 0 };
      // Checks this condition before running the nested branch.
      if (path.includes('/results')) return verifiedResults;
      // Checks this condition before running the nested branch.
      if (path === '/v1/challenges' && options?.method === 'POST') {
        // Calls bodies.push with the supplied values.
        bodies.push(String(options.body));
        // Executes this line as the next step in the surrounding logic.
        createCalls += 1;
        // Checks this condition before running the nested branch.
        if (createCalls === 1) throw new Error('response interrupted');
        // Returns this result to the caller and ends the current function.
        return {
          // Defines the id field in the surrounding object or type.
          id: 'challenge-1',
          // Defines the shareCode field in the surrounding object or type.
          shareCode: 'private-code',
          // Defines the title field in the surrounding object or type.
          title: null,
          // Defines the creatorName field in the surrounding object or type.
          creatorName: null,
          // Defines the config field in the surrounding object or type.
          config: game.config,
          // Defines the expiresAt field in the surrounding object or type.
          expiresAt: new Date().toISOString(),
          // Defines the revoked field in the surrounding object or type.
          revoked: false,
          // Defines the completedCount field in the surrounding object or type.
          completedCount: 3,
          // Closes the expression, call, or declaration started above.
        };
        // Closes the expression, call, or declaration started above.
      }
      // Throws this error to report an invalid or failed operation.
      throw new Error(`Unexpected request: ${path}`);
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderLocalized with the supplied values.
    renderLocalized(<ChallengeCreator />);
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('radio', { name: 'Custom' }));
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Create challenge' }));
    // Waits for this asynchronous operation to complete.
    await screen.findByRole('alert');
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Create challenge' }));

    // Calls expect with the supplied values.
    expect(await screen.findByRole('heading', { name: 'Verified results' })).toBeVisible();
    // Computes and stores resultBoard for subsequent operations.
    const resultBoard = screen.getByRole('table', { name: 'Verified results' });
    // Calls expect with the supplied values.
    expect(
      // Calls screen.getByRole with the supplied values.
      screen.getByRole('region', { name: 'Scrollable verified results table' }),
      // Executes this line as the next step in the surrounding logic.
    ).toContainElement(resultBoard);
    // Calls expect with the supplied values.
    expect(
      // Calls within with the supplied values.
      within(resultBoard).getByRole('row', { name: /1 Breaker A1B2C3 won 1,420/ }),
      // Executes this line as the next step in the surrounding logic.
    ).toHaveTextContent('2 of 10');
    // Executes this line as the next step in the surrounding logic.
    const [first, second] = bodies.map(
      // Executes this line as the next step in the surrounding logic.
      (body) =>
        // Calls JSON.parse with the supplied values.
        JSON.parse(body) as {
          // Defines the idempotencyKey field in the surrounding object or type.
          idempotencyKey: string;
          // Defines the config field in the surrounding object or type.
          config: { codeLength: number; ranked: boolean };
          // Closes the expression, call, or declaration started above.
        },
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(second?.idempotencyKey).toBe(first?.idempotencyKey);
    // Calls expect with the supplied values.
    expect(first?.config).toMatchObject({ codeLength: 4, ranked: false });
    // Calls expect with the supplied values.
    expect(apiMock).toHaveBeenCalledWith('/v1/challenges/challenge-1/results?page=1&page_size=10');
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('manages returning challenges without reconstructing private share links', async () => {
    // Computes and stores owned for subsequent operations.
    const owned = {
      // Defines the id field in the surrounding object or type.
      id: 'challenge-2',
      // Defines the title field in the surrounding object or type.
      title: 'Returning puzzle',
      // Defines the showCreatorName field in the surrounding object or type.
      showCreatorName: true,
      // Defines the config field in the surrounding object or type.
      config: game.config,
      // Defines the revoked field in the surrounding object or type.
      revoked: false,
      // Defines the expiresAt field in the surrounding object or type.
      expiresAt: new Date(Date.now() + 86_400_000).toISOString(),
      // Defines the completedCount field in the surrounding object or type.
      completedCount: 2,
      // Defines the createdAt field in the surrounding object or type.
      createdAt: new Date().toISOString(),
      // Closes the expression, call, or declaration started above.
    };
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string, options?: RequestInit) => {
      // Checks this condition before running the nested branch.
      if (path === '/v1/challenges/mine?page=1&page_size=20')
        // Returns this result to the caller and ends the current function.
        return { items: [owned], page: 1, pageSize: 20, total: 1 };
      // Checks this condition before running the nested branch.
      if (path.endsWith('/results?page=1&page_size=10')) return verifiedResults;
      // Checks this condition before running the nested branch.
      if (path === '/v1/challenges/challenge-2' && options?.method === 'DELETE') return undefined;
      // Throws this error to report an invalid or failed operation.
      throw new Error(`Unexpected request: ${path}`);
      // Closes the expression, call, or declaration started above.
    });
    // Calls vi.spyOn with the supplied values.
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderLocalized with the supplied values.
    renderLocalized(<ChallengeCreator />);

    // Calls expect with the supplied values.
    expect(await screen.findByRole('heading', { name: 'Returning puzzle' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(screen.queryByDisplayValue(/challenge/i)).not.toBeInTheDocument();
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'View results' }));
    // Calls expect with the supplied values.
    expect(await screen.findByText('50%')).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Revoke challenge' }));

    // Calls expect with the supplied values.
    expect(await screen.findByText('Revoked')).toBeVisible();
    // Calls expect with the supplied values.
    expect(apiMock).toHaveBeenCalledWith('/v1/challenges/challenge-2', { method: 'DELETE' });
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('renders authoritative daily history and progressive achievement data on the profile', async () => {
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string) => {
      // Checks this condition before running the nested branch.
      if (path === '/v1/me/profile')
        // Returns this result to the caller and ends the current function.
        return {
          // Defines the id field in the surrounding object or type.
          id: 'user-1',
          // Defines the displayName field in the surrounding object or type.
          displayName: 'Ada',
          // Defines the isAnonymous field in the surrounding object or type.
          isAnonymous: false,
          // Defines the publicLeaderboards field in the surrounding object or type.
          publicLeaderboards: true,
          // Defines the createdAt field in the surrounding object or type.
          createdAt: '2026-07-01T00:00:00Z',
          // Closes the expression, call, or declaration started above.
        };
      // Checks this condition before running the nested branch.
      if (path === '/v1/me/stats') return profileStats;
      // Checks this condition before running the nested branch.
      if (path === '/v1/me/games?page=1&page_size=8')
        // Returns this result to the caller and ends the current function.
        return { items: [], page: 1, pageSize: 8, total: 0 };
      // Throws this error to report an invalid or failed operation.
      throw new Error(`Unexpected request: ${path}`);
      // Closes the expression, call, or declaration started above.
    });

    // Calls renderLocalized with the supplied values.
    renderLocalized(<ProfilePanel />);

    // Calls expect with the supplied values.
    expect(await screen.findByRole('heading', { name: 'Daily challenge history' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(document.querySelector('time[datetime="2026-07-15"]')).toHaveTextContent('Jul 15, 2026');
    // Calls expect with the supplied values.
    expect(screen.getByRole('progressbar', { name: 'Logic Week: 3 of 7' })).toHaveAttribute(
      // Supplies this item to the surrounding call or collection.
      'value',
      // Supplies this item to the surrounding call or collection.
      '3',
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(screen.getByRole('link', { name: /View all achievements/ })).toHaveAttribute(
      // Supplies this item to the surrounding call or collection.
      'href',
      // Supplies this item to the surrounding call or collection.
      '/achievements',
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('shows server-calculated Logic Week progress in the achievement record', async () => {
    // Calls apiMock.mockResolvedValue with the supplied values.
    apiMock.mockResolvedValue(profileStats);

    // Calls renderLocalized with the supplied values.
    renderLocalized(<AchievementsPanel />);

    // Calls expect with the supplied values.
    expect(await screen.findByRole('heading', { name: 'Logic Week' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(screen.getByText('3 of 7')).toBeVisible();
    // Calls expect with the supplied values.
    expect(screen.getByRole('progressbar', { name: 'Logic Week: 3 of 7' })).toHaveAttribute(
      // Supplies this item to the surrounding call or collection.
      'max',
      // Supplies this item to the surrounding call or collection.
      '7',
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('shows both lobby readiness states and confirms the current player through the ready endpoint', async () => {
    // Computes and stores waitingRoom for subsequent operations.
    const waitingRoom = {
      // Defines the id field in the surrounding object or type.
      id: 'room-1',
      // Defines the roomCode field in the surrounding object or type.
      roomCode: 'ABC123',
      // Defines the status field in the surrounding object or type.
      status: 'waiting',
      // Defines the config field in the surrounding object or type.
      config: game.config,
      // Defines the members field in the surrounding object or type.
      members: [
        // Begins the nested block or object completed below.
        {
          // Defines the userId field in the surrounding object or type.
          userId: 'user-1',
          // Defines the displayName field in the surrounding object or type.
          displayName: 'Ada',
          // Defines the connected field in the surrounding object or type.
          connected: true,
          // Defines the ready field in the surrounding object or type.
          ready: false,
          // Defines the attemptsUsed field in the surrounding object or type.
          attemptsUsed: 0,
          // Defines the completed field in the surrounding object or type.
          completed: false,
          // Defines the gameId field in the surrounding object or type.
          gameId: 'game-1',
          // Closes the expression, call, or declaration started above.
        },
        // Begins the nested block or object completed below.
        {
          // Defines the userId field in the surrounding object or type.
          userId: 'user-2',
          // Defines the displayName field in the surrounding object or type.
          displayName: 'Lin',
          // Defines the connected field in the surrounding object or type.
          connected: true,
          // Defines the ready field in the surrounding object or type.
          ready: true,
          // Defines the attemptsUsed field in the surrounding object or type.
          attemptsUsed: 0,
          // Defines the completed field in the surrounding object or type.
          completed: false,
          // Defines the gameId field in the surrounding object or type.
          gameId: null,
          // Closes the expression, call, or declaration started above.
        },
        // Closes the expression, call, or declaration started above.
      ],
      // Defines the winnerId field in the surrounding object or type.
      winnerId: null,
      // Defines the isTie field in the surrounding object or type.
      isTie: false,
      // Defines the expiresAt field in the surrounding object or type.
      expiresAt: new Date().toISOString(),
      // Defines the eventSequence field in the surrounding object or type.
      eventSequence: 0,
      // Closes the expression, call, or declaration started above.
    };
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(
      // Continues the surrounding operation with this required value or expression.
      async (path: string, options?: RequestInit) =>
        // Executes this line as the next step in the surrounding logic.
        options?.method === 'POST' && path.endsWith('/ready')
          ? // Continues the surrounding operation with this required value or expression.
            // Begins the nested block or object completed below.
            {
              // Supplies this item to the surrounding call or collection.
              ...waitingRoom,
              // Defines the members field in the surrounding object or type.
              members: waitingRoom.members.map(
                // Continues the surrounding operation with this required value or expression.
                (member) =>
                  // Supplies this item to the surrounding call or collection.
                  member.userId === 'user-1' ? { ...member, ready: true } : member,
                // Closes the expression, call, or declaration started above.
              ),
              // Closes the expression, call, or declaration started above.
            }
          : // Continues the surrounding operation with this required value or expression.
            // Supplies this item to the surrounding call or collection.
            waitingRoom,
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderLocalized with the supplied values.
    renderLocalized(<RoomLobby roomId="room-1" />);

    // Calls expect with the supplied values.
    expect((await screen.findAllByText('Ready')).length).toBeGreaterThanOrEqual(1);
    // Calls expect with the supplied values.
    expect(screen.getByText('Not ready')).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'I’m ready' }));
    // Calls expect with the supplied values.
    expect(await screen.findByText('You’re ready. Waiting for the other player.')).toBeVisible();
    // Calls expect with the supplied values.
    expect(apiMock).toHaveBeenCalledWith('/v1/rooms/room-1/ready', { method: 'POST' });
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('preserves a mixed-case base64url room invite byte-for-byte when joining', async () => {
    // Computes and stores invite for subsequent operations.
    const invite = 'AbCd_ef-GhIjKlMnOpQrStUvWxYz0123456789';
    // Executes this line as the next step in the surrounding logic.
    searchParamsState.value = `code=${invite}`;
    // Calls apiMock.mockResolvedValue with the supplied values.
    apiMock.mockResolvedValue({ id: 'room-1', status: 'waiting', members: [] });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderLocalized with the supplied values.
    renderLocalized(<RoomEntry />);

    // Computes and stores input for subsequent operations.
    const input = screen.getByRole('textbox', { name: 'Invite code' });
    // Calls expect with the supplied values.
    expect(input).toHaveValue(invite);
    // Calls expect with the supplied values.
    expect(input).toHaveAttribute('autocapitalize', 'none');
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Join room' }));

    // Calls expect with the supplied values.
    expect(apiMock).toHaveBeenCalledWith(`/v1/rooms/${invite}/join`, { method: 'POST' });
    // Calls expect with the supplied values.
    expect(pushMock).toHaveBeenCalledWith('/rooms/room-1');
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('sends explicit deletion confirmation and directs recent-auth failures to sign-in', async () => {
    // Executes this line as the next step in the surrounding logic.
    const { ApiError } = await import('@/lib/api');
    // Calls apiMock.mockRejectedValue with the supplied values.
    apiMock.mockRejectedValue(
      // Begins the nested block or object completed below.
      new ApiError(401, {
        // Defines the code field in the surrounding object or type.
        code: 'RECENT_AUTH_REQUIRED',
        // Defines the message field in the surrounding object or type.
        message: 'Sign in again',
        // Defines the requestId field in the surrounding object or type.
        requestId: 'request-1',
        // Closes the expression, call, or declaration started above.
      }),
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderLocalized with the supplied values.
    renderLocalized(<AccountPanel />);
    // Waits for this asynchronous operation to complete.
    await user.type(screen.getByRole('textbox', { name: 'Type DELETE to confirm' }), 'DELETE');
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Permanently delete account' }));

    // Calls expect with the supplied values.
    expect(await screen.findByRole('alert')).toHaveTextContent(
      // Supplies this item to the surrounding call or collection.
      'For your protection, sign in again before deleting this account.',
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(screen.getByRole('link', { name: 'Sign in again' })).toHaveAttribute('href', '/auth');
    // Calls expect with the supplied values.
    expect(apiMock).toHaveBeenCalledWith('/v1/me', {
      // Defines the method field in the surrounding object or type.
      method: 'DELETE',
      // Defines the body field in the surrounding object or type.
      body: JSON.stringify({ confirmation: 'DELETE' }),
      // Closes the expression, call, or declaration started above.
    });
    // Calls expect with the supplied values.
    expect(signOutMock).not.toHaveBeenCalled();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('keeps websocket tickets out of URLs and rejects malformed realtime envelopes', async () => {
    // Declares the FakeWebSocket data shape or implementation.
    class FakeWebSocket {
      // Executes this line as the next step in the surrounding logic.
      static OPEN = 1;
      // Executes this line as the next step in the surrounding logic.
      static latest: FakeWebSocket | null = null;
      // Provides the readyState value to the surrounding call or element.
      readyState = 0;
      // Defines the onopen field in the surrounding object or type.
      onopen: (() => void) | null = null;
      // Defines the onmessage field in the surrounding object or type.
      onmessage: ((message: MessageEvent) => void) | null = null;
      // Defines the onclose field in the surrounding object or type.
      onclose: (() => void) | null = null;
      // Defines the onerror field in the surrounding object or type.
      onerror: (() => void) | null = null;
      // Provides the send value to the surrounding call or element.
      send = vi.fn();
      // Provides the close value to the surrounding call or element.
      close = vi.fn();
      // Calls constructor with the supplied values.
      constructor(
        // Supplies this item to the surrounding call or collection.
        readonly url: string,
        // Supplies this item to the surrounding call or collection.
        readonly protocols: string[],
        // Begins the nested block or object completed below.
      ) {
        // Executes this line as the next step in the surrounding logic.
        FakeWebSocket.latest = this;
        // Closes the expression, call, or declaration started above.
      }
      // Closes the expression, call, or declaration started above.
    }
    // Executes this line as the next step in the surrounding logic.
    globalThis.WebSocket = FakeWebSocket as unknown as typeof WebSocket;
    // Computes and stores activeRoom for subsequent operations.
    const activeRoom = {
      // Defines the id field in the surrounding object or type.
      id: 'room-1',
      // Defines the roomCode field in the surrounding object or type.
      roomCode: null,
      // Defines the status field in the surrounding object or type.
      status: 'active',
      // Defines the config field in the surrounding object or type.
      config: game.config,
      // Defines the members field in the surrounding object or type.
      members: [
        // Begins the nested block or object completed below.
        {
          // Defines the userId field in the surrounding object or type.
          userId: 'user-1',
          // Defines the displayName field in the surrounding object or type.
          displayName: 'Ada',
          // Defines the connected field in the surrounding object or type.
          connected: true,
          // Defines the ready field in the surrounding object or type.
          ready: true,
          // Defines the attemptsUsed field in the surrounding object or type.
          attemptsUsed: 0,
          // Defines the completed field in the surrounding object or type.
          completed: false,
          // Defines the gameId field in the surrounding object or type.
          gameId: 'game-1',
          // Closes the expression, call, or declaration started above.
        },
        // Begins the nested block or object completed below.
        {
          // Defines the userId field in the surrounding object or type.
          userId: 'user-2',
          // Defines the displayName field in the surrounding object or type.
          displayName: 'Lin',
          // Defines the connected field in the surrounding object or type.
          connected: false,
          // Defines the ready field in the surrounding object or type.
          ready: true,
          // Defines the attemptsUsed field in the surrounding object or type.
          attemptsUsed: 0,
          // Defines the completed field in the surrounding object or type.
          completed: false,
          // Defines the gameId field in the surrounding object or type.
          gameId: null,
          // Closes the expression, call, or declaration started above.
        },
        // Closes the expression, call, or declaration started above.
      ],
      // Defines the winnerId field in the surrounding object or type.
      winnerId: null,
      // Defines the isTie field in the surrounding object or type.
      isTie: false,
      // Defines the expiresAt field in the surrounding object or type.
      expiresAt: new Date().toISOString(),
      // Defines the eventSequence field in the surrounding object or type.
      eventSequence: 0,
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores currentRoom for subsequent operations.
    let currentRoom = activeRoom;
    // Computes and stores currentGame for subsequent operations.
    let currentGame = { ...game, mode: 'duel' };
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(
      // Continues the surrounding operation with this required value or expression.
      async (path: string) =>
        // Calls path.endsWith with the supplied values.
        path.endsWith('/ws-ticket')
          ? // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            { ticket: 'private_ticket', expiresAt: new Date().toISOString() }
          : // Continues the surrounding operation with this required value or expression.
            // Executes this line as the next step in the surrounding logic.
            path.startsWith('/v1/games/')
            ? // Continues the surrounding operation with this required value or expression.
              // Executes this line as the next step in the surrounding logic.
              currentGame
            : // Continues the surrounding operation with this required value or expression.
              // Supplies this item to the surrounding call or collection.
              currentRoom,
      // Closes the expression, call, or declaration started above.
    );
    // Calls renderLocalized with the supplied values.
    renderLocalized(<DuelPanel roomId="room-1" />);
    // Waits for this asynchronous operation to complete.
    await waitFor(() => expect(FakeWebSocket.latest).not.toBeNull());
    // Computes and stores connectedSocket for subsequent operations.
    const connectedSocket = FakeWebSocket.latest;
    // Calls expect with the supplied values.
    expect(connectedSocket?.url).toBe('wss://api.example.test/v1/rooms/room-1/events?after=0');
    // Calls expect with the supplied values.
    expect(connectedSocket?.protocols).toEqual(['cipherboard-v1', 'ticket.private_ticket']);
    // Checks this condition before running the nested branch.
    if (!connectedSocket) throw new Error('socket not created');
    // Executes this line as the next step in the surrounding logic.
    connectedSocket.readyState = FakeWebSocket.OPEN;
    // Calls fireEvent with the supplied values.
    fireEvent(window, new Event('focus'));
    // Executes this line as the next step in the surrounding logic.
    connectedSocket.onopen?.();
    // Waits for this asynchronous operation to complete.
    await screen.findByText('Opponent progress');
    // A connection-state rerender must not tear down and replace a healthy socket.
    expect(FakeWebSocket.latest).toBe(connectedSocket);
    // Begins the nested block or object completed below.
    connectedSocket.onmessage?.({
      // Defines the data field in the surrounding object or type.
      data: JSON.stringify({
        // Defines the version field in the surrounding object or type.
        version: 1,
        // Defines the sequence field in the surrounding object or type.
        sequence: 5,
        // Defines the type field in the surrounding object or type.
        type: 'snapshot',
        // Defines the payload field in the surrounding object or type.
        payload: {
          // Supplies this item to the surrounding call or collection.
          ...activeRoom,
          // Defines the eventSequence field in the surrounding object or type.
          eventSequence: 5,
          // Defines the members field in the surrounding object or type.
          members: activeRoom.members.map(
            // Continues the surrounding operation with this required value or expression.
            (member) =>
              // Supplies this item to the surrounding call or collection.
              member.userId === 'user-2' ? { ...member, attemptsUsed: 3 } : member,
            // Closes the expression, call, or declaration started above.
          ),
          // Closes the expression, call, or declaration started above.
        },
        // Closes the expression, call, or declaration started above.
      }),
      // Executes this line as the next step in the surrounding logic.
    } as MessageEvent);
    // The snapshot can be stale while the opponent's socket finishes connecting.
    expect(await screen.findByText('Disconnected')).toBeVisible();
    // Begins the nested block or object completed below.
    connectedSocket.onmessage?.({
      // Defines the data field in the surrounding object or type.
      data: JSON.stringify({
        // Defines the version field in the surrounding object or type.
        version: 1,
        // Presence is ephemeral and does not consume the durable room sequence.
        sequence: null,
        // Defines the type field in the surrounding object or type.
        type: 'presence',
        // Defines the payload field in the surrounding object or type.
        payload: { userId: 'user-2', connected: true },
        // Closes the expression, call, or declaration started above.
      }),
      // Closes the expression, call, or declaration started above.
    } as MessageEvent);
    // The live presence event must replace the stale disconnected snapshot state.
    expect(await screen.findByText('Connected')).toBeVisible();
    // Begins the nested block or object completed below.
    connectedSocket.onmessage?.({
      // Defines the data field in the surrounding object or type.
      data: JSON.stringify({
        // Defines the version field in the surrounding object or type.
        version: 1,
        // Defines the sequence field in the surrounding object or type.
        sequence: 4,
        // Defines the type field in the surrounding object or type.
        type: 'opponent_progress',
        // Defines the payload field in the surrounding object or type.
        payload: { userId: 'user-2', attemptsUsed: 1, completed: false },
        // Closes the expression, call, or declaration started above.
      }),
      // Executes this line as the next step in the surrounding logic.
    } as MessageEvent);
    // Calls expect with the supplied values.
    expect(await screen.findByText('Opponent attempts: 3')).toBeVisible();

    // Begins the nested block or object completed below.
    connectedSocket.onmessage?.({
      // Defines the data field in the surrounding object or type.
      data: JSON.stringify({
        // Defines the version field in the surrounding object or type.
        version: 1,
        // Defines the sequence field in the surrounding object or type.
        sequence: 6,
        // Defines the type field in the surrounding object or type.
        type: 'attempt_result',
        // Defines the payload field in the surrounding object or type.
        payload: {
          // Defines the number field in the surrounding object or type.
          number: 1,
          // Defines the guess field in the surrounding object or type.
          guess: ['R', 'B', 'G', 'Y'],
          // Defines the feedback field in the surrounding object or type.
          feedback: { black: 4, white: 0 },
          // Defines the status field in the surrounding object or type.
          status: 'won',
          // Closes the expression, call, or declaration started above.
        },
        // Closes the expression, call, or declaration started above.
      }),
      // Executes this line as the next step in the surrounding logic.
    } as MessageEvent);
    // Waits for this asynchronous operation to complete.
    await screen.findByText('Code broken');
    // Calls expect with the supplied values.
    expect(analyticsMock).not.toHaveBeenCalledWith('duel_completed', expect.anything());

    // Provides the currentRoom value to the surrounding call or element.
    currentRoom = {
      // Supplies this item to the surrounding call or collection.
      ...activeRoom,
      // Defines the status field in the surrounding object or type.
      status: 'completed',
      // Defines the winnerId field in the surrounding object or type.
      winnerId: null,
      // Defines the isTie field in the surrounding object or type.
      isTie: true,
      // Defines the eventSequence field in the surrounding object or type.
      eventSequence: 7,
      // Closes the expression, call, or declaration started above.
    };
    // Provides the currentGame value to the surrounding call or element.
    currentGame = {
      // Supplies this item to the surrounding call or collection.
      ...currentGame,
      // Defines the status field in the surrounding object or type.
      status: 'won',
      // Defines the attemptsUsed field in the surrounding object or type.
      attemptsUsed: 1,
      // Defines the attemptsRemaining field in the surrounding object or type.
      attemptsRemaining: 9,
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores completedEvent for subsequent operations.
    const completedEvent = {
      // Defines the data field in the surrounding object or type.
      data: JSON.stringify({
        // Defines the version field in the surrounding object or type.
        version: 1,
        // Defines the sequence field in the surrounding object or type.
        sequence: 7,
        // Defines the type field in the surrounding object or type.
        type: 'room_completed',
        // Defines the payload field in the surrounding object or type.
        payload: { winnerId: null, isTie: true, reason: 'tie_window' },
        // Closes the expression, call, or declaration started above.
      }),
      // Executes this line as the next step in the surrounding logic.
    } as MessageEvent;
    // Executes this line as the next step in the surrounding logic.
    connectedSocket.onmessage?.(completedEvent);
    // Calls expect with the supplied values.
    expect(await screen.findByText('The duel ended in a tie')).toBeVisible();
    // Executes this line as the next step in the surrounding logic.
    connectedSocket.onmessage?.(completedEvent);
    // Waits for this asynchronous operation to complete.
    await waitFor(
      // Continues the surrounding operation with this required value or expression.
      () =>
        // Calls expect with the supplied values.
        expect(analyticsMock.mock.calls.filter(([name]) => name === 'duel_completed')).toHaveLength(
          // Supplies this item to the surrounding call or collection.
          1,
          // Closes the expression, call, or declaration started above.
        ),
      // Closes the expression, call, or declaration started above.
    );
    // Executes this line as the next step in the surrounding logic.
    connectedSocket.onmessage?.({ data: '{malformed' } as MessageEvent);
    // Calls expect with the supplied values.
    expect(await screen.findByRole('alert')).toHaveTextContent('The live room protocol changed.');
    // Calls expect with the supplied values.
    expect(connectedSocket.close).toHaveBeenCalledWith(1002, 'Invalid event envelope');
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
