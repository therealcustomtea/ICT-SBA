import { NextIntlClientProvider } from 'next-intl';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe } from 'jest-axe';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/en.json';
import { ApiError, type Game } from '@/lib/api';
import { GameBoard } from './game-board';

const { apiMock } = vi.hoisted(() => ({ apiMock: vi.fn() }));

vi.mock('@/lib/api', () => {
  class MockApiError extends Error {
    constructor(
      readonly status: number,
      readonly body: { code: string; message: string; requestId: string },
    ) {
      super(body.message);
    }
  }
  return { ApiError: MockApiError, useApi: () => apiMock };
});
vi.mock('@/lib/use-product-analytics', () => ({ useProductAnalytics: () => vi.fn() }));
vi.mock('@/i18n/navigation', () => ({
  Link: ({ children, href, ...props }: React.ComponentProps<'a'>) => (
    <a href={String(href)} {...props}>
      {children}
    </a>
  ),
}));

const activeGame: Game = {
  id: 'game-1',
  mode: 'solo',
  difficulty: 'normal',
  status: 'active',
  config: {
    colours: ['R', 'B', 'G', 'Y', 'W', 'K'],
    codeLength: 4,
    maxAttempts: 10,
    duplicatesAllowed: true,
    codeMaker: 'computer',
    visibility: 'public',
    ranked: true,
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
  ranked: true,
};

const wonGame: Game = {
  ...activeGame,
  status: 'won',
  attempts: [
    {
      number: 1,
      guess: ['R', 'B', 'G', 'Y'],
      feedback: { black: 4, white: 0 },
      submittedAt: new Date().toISOString(),
    },
  ],
  attemptsUsed: 1,
  attemptsRemaining: 9,
  completedAt: new Date().toISOString(),
  score: 1000,
  scoreBreakdown: { attempts: 900, difficulty: 100, time: 0, total: 1000, version: 'score_v1' },
  secret: ['R', 'B', 'G', 'Y'],
};

function renderBoard(initialGameId: string | null = 'game-1') {
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <GameBoard
        title="Code-breaking board"
        intro="Use logic to break the code."
        initialGameId={initialGameId ?? undefined}
      />
    </NextIntlClientProvider>,
  );
}

describe('GameBoard accessibility', () => {
  afterEach(cleanup);

  beforeEach(() => {
    apiMock.mockReset();
    localStorage.clear();
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
  });

  it('supports keyboard-only play, announces feedback, and moves focus to the result', async () => {
    apiMock.mockImplementation(async (path: string) =>
      path.endsWith('/attempts') ? wonGame : activeGame,
    );
    const user = userEvent.setup();
    const { container } = renderBoard();
    const firstSlot = await screen.findByRole('button', { name: 'Position 1: empty' });

    expect(screen.getByRole('region', { name: 'Submitted guess board' })).toBeVisible();
    expect(firstSlot).toHaveAttribute('aria-pressed', 'true');
    firstSlot.focus();

    for (const [key, position] of [
      ['1', 2],
      ['2', 3],
      ['3', 4],
    ] as const) {
      await user.keyboard(key);
      await waitFor(() =>
        expect(screen.getByRole('button', { name: `Position ${position}: empty` })).toHaveFocus(),
      );
    }
    await user.keyboard('4');

    const submit = screen.getByRole('button', { name: 'Submit guess' });
    expect(submit).toBeEnabled();
    submit.focus();
    fireEvent.keyDown(submit, { key: 'Enter' });
    await user.click(submit);

    expect(await screen.findByRole('heading', { level: 2, name: 'Code broken' })).toBeVisible();
    const attemptRequests = apiMock.mock.calls.filter(([path]) =>
      String(path).endsWith('/attempts'),
    );
    expect(attemptRequests).toHaveLength(1);
    expect(screen.getByText(/Guess 1: 4 exact-position clues/)).toBeInTheDocument();
    await waitFor(() => expect(container.querySelector('.result-panel')).toHaveFocus());
    await user.click(screen.getByRole('button', { name: 'Share result' }));
    expect(screen.getByText('Result copied.')).toBeInTheDocument();
    expect((await axe(container)).violations).toEqual([]);
    await user.click(screen.getByRole('button', { name: 'Play again' }));
    expect(screen.getByRole('button', { name: 'Begin game' })).toBeEnabled();
  });

  it('does not enable submission when keyboard selection leaves empty slots', async () => {
    apiMock.mockResolvedValue(activeGame);
    const user = userEvent.setup();
    renderBoard();
    const fourthSlot = await screen.findByRole('button', { name: 'Position 4: empty' });

    await user.click(fourthSlot);
    await user.keyboard('1');

    expect(screen.getByRole('button', { name: 'Position 4: Red circle' })).toHaveClass(
      'filled',
      'peg-R',
    );
    expect(screen.getByRole('button', { name: 'Position 4: Red circle' })).not.toHaveClass('empty');
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeDisabled();
  });

  it('starts a new game from the introduction', async () => {
    apiMock.mockResolvedValue(activeGame);
    const user = userEvent.setup();
    renderBoard(null);

    await user.click(screen.getByRole('button', { name: 'Begin game' }));

    expect(await screen.findByRole('region', { name: 'Submitted guess board' })).toBeVisible();
    expect(apiMock).toHaveBeenCalledWith('/v1/games', expect.objectContaining({ method: 'POST' }));
  });

  it('announces initial-load and start failures', async () => {
    apiMock.mockRejectedValue(new Error('unavailable'));
    renderBoard();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The request could not be completed. Please try again.',
    );

    cleanup();
    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <GameBoard title="Code-breaking board" />
      </NextIntlClientProvider>,
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Begin game' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The request could not be completed. Please try again.',
    );
  });

  it('supports arrow, delete, clear, offline, and board-level submit keys', async () => {
    localStorage.setItem('cipherboard:row:game-1', '{invalid json');
    apiMock.mockImplementation(async (path: string) => {
      if (path.endsWith('/attempts')) throw new Error('submission rejected');
      return activeGame;
    });
    const user = userEvent.setup();
    renderBoard();
    const firstSlot = await screen.findByRole('button', { name: 'Position 1: empty' });

    firstSlot.focus();
    await user.keyboard('{ArrowRight}');
    expect(screen.getByRole('button', { name: 'Position 2: empty' })).toHaveFocus();
    await user.keyboard('2');
    await user.keyboard('{ArrowLeft}{Backspace}');
    expect(screen.getByRole('button', { name: 'Position 2: empty' })).toBeVisible();

    firstSlot.focus();
    for (const key of ['1', '2', '3', '4']) await user.keyboard(key);
    await user.click(screen.getByRole('button', { name: 'Clear row' }));
    expect(firstSlot).toHaveFocus();

    for (const key of ['1', '2', '3', '4']) await user.keyboard(key);
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
    fireEvent(window, new Event('offline'));
    expect(
      await screen.findByText('Your unsubmitted row is preserved. Reconnect before submitting.'),
    ).toBeVisible();
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeDisabled();

    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    fireEvent(window, new Event('online'));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Submit guess' })).toBeEnabled());
    const workspace = screen.getByRole('region', { name: 'Code-breaking board' });
    fireEvent.keyDown(workspace, { key: 'Enter' });
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The request could not be completed. Please try again.',
    );
  });

  it('reuses the same idempotency key when an uncertain attempt is retried', async () => {
    apiMock.mockImplementation(async (path: string) => {
      if (path.endsWith('/attempts')) throw new Error('connection interrupted');
      return activeGame;
    });
    const user = userEvent.setup();
    renderBoard();
    await screen.findByRole('button', { name: 'Position 1: empty' });
    for (const color of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square']) {
      await user.click(screen.getByRole('button', { name: new RegExp(`Choose ${color}`) }));
    }

    await user.click(screen.getByRole('button', { name: 'Submit guess' }));
    await screen.findByRole('alert');
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Retry game restore' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Submit guess' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: 'Submit guess' }));
    await waitFor(() =>
      expect(
        apiMock.mock.calls.filter(([path]) => String(path).endsWith('/attempts')),
      ).toHaveLength(2),
    );

    const attempts = apiMock.mock.calls.filter(([path]) => String(path).endsWith('/attempts'));
    const first = JSON.parse(String((attempts[0]?.[1] as RequestInit).body)) as {
      idempotencyKey: string;
    };
    const second = JSON.parse(String((attempts[1]?.[1] as RequestInit).body)) as {
      idempotencyKey: string;
    };
    expect(second.idempotencyKey).toBe(first.idempotencyKey);
    expect(
      JSON.parse(localStorage.getItem('cipherboard:pending-attempt:game-1') ?? '{}'),
    ).toMatchObject({ idempotencyKey: first.idempotencyKey, guess: ['R', 'B', 'G', 'Y'] });
  });

  it('keeps a deterministic duplicate validation failure editable without resyncing', async () => {
    const noDuplicatesGame: Game = {
      ...activeGame,
      config: { ...activeGame.config, duplicatesAllowed: false },
    };
    apiMock.mockImplementation(async (path: string) => {
      if (path.endsWith('/attempts'))
        throw new ApiError(422, {
          code: 'DUPLICATES_NOT_ALLOWED',
          message: 'This game does not allow duplicate colours.',
          requestId: 'request-1',
        });
      return noDuplicatesGame;
    });
    const user = userEvent.setup();
    renderBoard();
    await screen.findByRole('button', { name: 'Position 1: empty' });
    const red = screen.getByRole('button', { name: /Choose Red circle/ });
    for (let index = 0; index < 4; index += 1) await user.click(red);

    await user.click(screen.getByRole('button', { name: 'Submit guess' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'This game does not allow repeated pegs. Change the repeated peg and submit again.',
    );
    expect(screen.queryByRole('button', { name: 'Retry game restore' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Position 1: Red circle' })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Position 4: Red circle' })).toBeVisible();
    expect(localStorage.getItem('cipherboard:pending-attempt:game-1')).toBeNull();
    await user.click(screen.getByRole('button', { name: 'Clear row' }));
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeDisabled();
  });

  it('reconciles an accepted attempt after reconnect without submitting it twice', async () => {
    const progressedGame: Game = {
      ...activeGame,
      attempts: [
        {
          number: 1,
          guess: ['R', 'B', 'G', 'Y'],
          feedback: { black: 0, white: 2 },
          submittedAt: new Date().toISOString(),
        },
      ],
      attemptsUsed: 1,
      attemptsRemaining: 9,
    };
    let gameLoads = 0;
    apiMock.mockImplementation(async (path: string) => {
      if (path.endsWith('/attempts')) throw new Error('response lost');
      if (path === '/v1/games/game-1') {
        gameLoads += 1;
        return gameLoads === 1 ? activeGame : progressedGame;
      }
      return { bestScoreByDifficulty: {} };
    });
    const user = userEvent.setup();
    renderBoard();
    await screen.findByRole('button', { name: 'Position 1: empty' });
    for (const color of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square']) {
      await user.click(screen.getByRole('button', { name: new RegExp(`Choose ${color}`) }));
    }
    await user.click(screen.getByRole('button', { name: 'Submit guess' }));
    await screen.findByRole('alert');

    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
    fireEvent(window, new Event('offline'));
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    fireEvent(window, new Event('online'));

    expect(
      await screen.findByRole('group', {
        name: 'Attempt 1: 0 exact-position and 2 correct-colour clues',
      }),
    ).toBeVisible();
    expect(screen.getByRole('button', { name: 'Position 1: empty' })).toBeVisible();
    expect(localStorage.getItem('cipherboard:pending-attempt:game-1')).toBeNull();
    expect(apiMock.mock.calls.filter(([path]) => String(path).endsWith('/attempts'))).toHaveLength(
      1,
    );
  });

  it('confirms abandonment and focuses its terminal result', async () => {
    const abandonedGame: Game = {
      ...activeGame,
      status: 'abandoned',
      completedAt: new Date().toISOString(),
      score: 0,
    };
    apiMock.mockImplementation(async (path: string) =>
      path.endsWith('/abandon') ? abandonedGame : activeGame,
    );
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const user = userEvent.setup();
    const { container } = renderBoard();

    await screen.findByRole('button', { name: 'Abandon game' });
    await user.click(screen.getByRole('button', { name: 'Abandon game' }));

    expect(await screen.findByRole('heading', { level: 2, name: 'Game abandoned' })).toBeVisible();
    await waitFor(() => expect(container.querySelector('.result-panel')).toHaveFocus());
  });

  it('starts daily and friend replays explicitly as unranked practice', async () => {
    const practiceGame: Game = {
      ...activeGame,
      mode: 'practice',
      ranked: false,
      config: { ...activeGame.config, ranked: false },
    };
    apiMock.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === '/v1/daily/start' && options?.method === 'POST') return practiceGame;
      if (path === '/v1/me/stats') return { bestScoreByDifficulty: {} };
      return wonGame;
    });
    const user = userEvent.setup();
    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <GameBoard
          title="Daily challenge"
          initialGameId="game-1"
          startEndpoint="/v1/daily/start"
          replayBody={{ practice: true }}
          replayLabel="Play again unranked"
        />
      </NextIntlClientProvider>,
    );

    await user.click(await screen.findByRole('button', { name: 'Play again unranked' }));

    expect(apiMock).toHaveBeenCalledWith('/v1/daily/start', {
      method: 'POST',
      body: JSON.stringify({ practice: true }),
    });
    expect(await screen.findByText('Practice')).toBeVisible();
  });

  it('restores the active daily game and its unsubmitted row after a remount', async () => {
    const dailyGame: Game = { ...activeGame, id: 'daily-game-1', mode: 'daily' };
    localStorage.setItem('cipherboard:daily:daily-challenge-1:active-game', dailyGame.id);
    localStorage.setItem(`cipherboard:row:${dailyGame.id}`, JSON.stringify(['R', 'B', 'G', 'Y']));
    apiMock.mockImplementation(async (path: string) => {
      if (path === `/v1/games/${dailyGame.id}`) return dailyGame;
      return { bestScoreByDifficulty: {} };
    });

    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <GameBoard
          title="Daily challenge"
          startEndpoint="/v1/daily/start"
          startBody={{ practice: false }}
          dailyChallengeId="daily-challenge-1"
        />
      </NextIntlClientProvider>,
    );

    expect(await screen.findByRole('button', { name: 'Position 4: Yellow square' })).toBeVisible();
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeEnabled();
    expect(apiMock).toHaveBeenCalledWith(`/v1/games/${dailyGame.id}`);
    expect(
      apiMock.mock.calls.some(
        ([path, options]) => path === '/v1/daily/start' && options?.method === 'POST',
      ),
    ).toBe(false);
  });

  it('clears an inaccessible stored daily game and returns to a startable state', async () => {
    const storageKey = 'cipherboard:daily:daily-challenge-1:active-game';
    localStorage.setItem(storageKey, 'stale-game-id');
    apiMock.mockImplementation(async (path: string) => {
      if (path === '/v1/games/stale-game-id') throw new Error('not found');
      if (path === '/v1/daily/start') return { ...activeGame, id: 'daily-game-2', mode: 'daily' };
      return { bestScoreByDifficulty: {} };
    });
    const user = userEvent.setup();

    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <GameBoard
          title="Daily challenge"
          startEndpoint="/v1/daily/start"
          startBody={{ practice: false }}
          dailyChallengeId="daily-challenge-1"
        />
      </NextIntlClientProvider>,
    );

    const start = await screen.findByRole('button', { name: 'Begin game' });
    expect(start).toBeEnabled();
    expect(localStorage.getItem(storageKey)).toBeNull();
    await user.click(start);
    expect(await screen.findByRole('region', { name: 'Submitted guess board' })).toBeVisible();
    expect(localStorage.getItem(storageKey)).toBe('daily-game-2');
  });

  it('shows only achievements earned during the just-completed game', async () => {
    let statsCalls = 0;
    apiMock.mockImplementation(async (path: string) => {
      if (path === '/v1/me/stats') {
        statsCalls += 1;
        return {
          bestScoreByDifficulty: { normal: 1000 },
          achievements: statsCalls === 1 ? ['first_break'] : ['first_break', 'one_shot'],
        };
      }
      if (path.startsWith('/v1/leaderboards')) return { currentUserRank: 7 };
      if (path.endsWith('/attempts')) return wonGame;
      return activeGame;
    });
    const user = userEvent.setup();
    renderBoard();
    await screen.findByRole('button', { name: 'Position 1: empty' });
    await waitFor(() => expect(statsCalls).toBe(1));

    for (const color of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square']) {
      await user.click(screen.getByRole('button', { name: new RegExp(`Choose ${color}`) }));
    }
    await user.click(screen.getByRole('button', { name: 'Submit guess' }));

    expect(await screen.findByRole('heading', { name: 'Achievements earned' })).toBeVisible();
    expect(screen.getByText('One Shot')).toBeVisible();
    expect(screen.queryByText('First break')).not.toBeInTheDocument();
    expect(screen.getByText('Leaderboard position: 7')).toBeVisible();
  });
});
