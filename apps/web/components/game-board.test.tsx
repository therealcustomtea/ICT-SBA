// Imports the dependency used by this module.
import { NextIntlClientProvider } from 'next-intl';
// Imports the dependency used by this module.
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
// Imports the dependency used by this module.
import userEvent from '@testing-library/user-event';
// Imports the dependency used by this module.
import { axe } from 'jest-axe';
// Imports the dependency used by this module.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
// Imports the dependency used by this module.
import messages from '@/messages/en.json';
// Imports the dependency used by this module.
import { ApiError, type Game } from '@/lib/api';
// Imports the dependency used by this module.
import { GameBoard } from './game-board';

// Executes this line as the next step in the surrounding logic.
const { apiMock } = vi.hoisted(() => ({ apiMock: vi.fn() }));

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
  return { ApiError: MockApiError, useApi: () => apiMock };
  // Closes the expression, call, or declaration started above.
});
// Calls vi.mock with the supplied values.
vi.mock('@/lib/use-product-analytics', () => ({ useProductAnalytics: () => vi.fn() }));
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
  // Closes the expression, call, or declaration started above.
}));

// Computes and stores activeGame for subsequent operations.
const activeGame: Game = {
  // Defines the id field in the surrounding object or type.
  id: 'game-1',
  // Defines the mode field in the surrounding object or type.
  mode: 'solo',
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
    codeMaker: 'computer',
    // Defines the visibility field in the surrounding object or type.
    visibility: 'public',
    // Defines the ranked field in the surrounding object or type.
    ranked: true,
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
  ranked: true,
  // Closes the expression, call, or declaration started above.
};

// Computes and stores wonGame for subsequent operations.
const wonGame: Game = {
  // Supplies this item to the surrounding call or collection.
  ...activeGame,
  // Defines the status field in the surrounding object or type.
  status: 'won',
  // Defines the attempts field in the surrounding object or type.
  attempts: [
    // Begins the nested block or object completed below.
    {
      // Defines the number field in the surrounding object or type.
      number: 1,
      // Defines the guess field in the surrounding object or type.
      guess: ['R', 'B', 'G', 'Y'],
      // Defines the feedback field in the surrounding object or type.
      feedback: { black: 4, white: 0 },
      // Defines the submittedAt field in the surrounding object or type.
      submittedAt: new Date().toISOString(),
      // Closes the expression, call, or declaration started above.
    },
    // Closes the expression, call, or declaration started above.
  ],
  // Defines the attemptsUsed field in the surrounding object or type.
  attemptsUsed: 1,
  // Defines the attemptsRemaining field in the surrounding object or type.
  attemptsRemaining: 9,
  // Defines the completedAt field in the surrounding object or type.
  completedAt: new Date().toISOString(),
  // Defines the score field in the surrounding object or type.
  score: 1000,
  // Defines the scoreBreakdown field in the surrounding object or type.
  scoreBreakdown: { attempts: 900, difficulty: 100, time: 0, total: 1000, version: 'score_v1' },
  // Defines the secret field in the surrounding object or type.
  secret: ['R', 'B', 'G', 'Y'],
  // Closes the expression, call, or declaration started above.
};

// Defines the renderBoard function and its callable behavior.
function renderBoard(initialGameId: string | null = 'game-1') {
  // Returns this result to the caller and ends the current function.
  return render(
    // Renders the NextIntlClientProvider interface element or component.
    <NextIntlClientProvider locale="en" messages={messages}>
      {/* Renders the GameBoard interface element or component. */}
      <GameBoard
        /* Provides the title value to the surrounding call or element. */
        title="Code-breaking board"
        /* Provides the intro value to the surrounding call or element. */
        intro="Use logic to break the code."
        /* Provides the initialGameId value to the surrounding call or element. */
        initialGameId={initialGameId ?? undefined}
        /* Executes this line as the next step in the surrounding logic. */
      />
      {/* Closes the NextIntlClientProvider interface element. */}
    </NextIntlClientProvider>,
    // Closes the expression, call, or declaration started above.
  );
  // Closes the expression, call, or declaration started above.
}

// Calls describe with the supplied values.
describe('GameBoard accessibility', () => {
  // Calls afterEach with the supplied values.
  afterEach(cleanup);

  // Calls beforeEach with the supplied values.
  beforeEach(() => {
    // Calls apiMock.mockReset with the supplied values.
    apiMock.mockReset();
    // Calls localStorage.clear with the supplied values.
    localStorage.clear();
    // Calls Object.defineProperty with the supplied values.
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('supports keyboard-only play, announces feedback, and moves focus to the result', async () => {
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(
      // Continues the surrounding operation with this required value or expression.
      async (path: string) =>
        // Calls path.endsWith with the supplied values.
        path.endsWith('/attempts') ? wonGame : activeGame,
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Executes this line as the next step in the surrounding logic.
    const { container } = renderBoard();
    // Computes and stores firstSlot for subsequent operations.
    const firstSlot = await screen.findByRole('button', { name: 'Position 1: empty' });

    // Calls expect with the supplied values.
    expect(screen.getByRole('region', { name: 'Submitted guess board' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(firstSlot).toHaveAttribute('aria-pressed', 'true');
    // Calls firstSlot.focus with the supplied values.
    firstSlot.focus();

    // Iterates through these values for the nested operation.
    for (const [key, position] of [
      // Supplies this item to the surrounding call or collection.
      ['1', 2],
      // Supplies this item to the surrounding call or collection.
      ['2', 3],
      // Supplies this item to the surrounding call or collection.
      ['3', 4],
      // Begins the nested block or object completed below.
    ] as const) {
      // Waits for this asynchronous operation to complete.
      await user.keyboard(key);
      // Waits for this asynchronous operation to complete.
      await waitFor(
        // Continues the surrounding operation with this required value or expression.
        () =>
          // Calls expect with the supplied values.
          expect(screen.getByRole('button', { name: `Position ${position}: empty` })).toHaveFocus(),
        // Closes the expression, call, or declaration started above.
      );
      // Closes the expression, call, or declaration started above.
    }
    // Waits for this asynchronous operation to complete.
    await user.keyboard('4');

    // Computes and stores submit for subsequent operations.
    const submit = screen.getByRole('button', { name: 'Submit guess' });
    // Calls expect with the supplied values.
    expect(submit).toBeEnabled();
    // Calls submit.focus with the supplied values.
    submit.focus();
    // Calls fireEvent.keyDown with the supplied values.
    fireEvent.keyDown(submit, { key: 'Enter' });
    // Waits for this asynchronous operation to complete.
    await user.click(submit);

    // Calls expect with the supplied values.
    expect(await screen.findByRole('heading', { level: 2, name: 'Code broken' })).toBeVisible();
    // Computes and stores attemptRequests for subsequent operations.
    const attemptRequests = apiMock.mock.calls.filter(
      // Continues the surrounding operation with this required value or expression.
      ([path]) =>
        // Calls String with the supplied values.
        String(path).endsWith('/attempts'),
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(attemptRequests).toHaveLength(1);
    // Calls expect with the supplied values.
    expect(screen.getByText(/Guess 1: 4 exact-position clues/)).toBeInTheDocument();
    // Waits for this asynchronous operation to complete.
    await waitFor(() => expect(container.querySelector('.result-panel')).toHaveFocus());
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Share result' }));
    // Calls expect with the supplied values.
    expect(screen.getByText('Result copied.')).toBeInTheDocument();
    // Calls expect with the supplied values.
    expect((await axe(container)).violations).toEqual([]);
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Play again' }));
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Begin game' })).toBeEnabled();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('does not enable submission when keyboard selection leaves empty slots', async () => {
    // Calls apiMock.mockResolvedValue with the supplied values.
    apiMock.mockResolvedValue(activeGame);
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderBoard with the supplied values.
    renderBoard();
    // Computes and stores fourthSlot for subsequent operations.
    const fourthSlot = await screen.findByRole('button', { name: 'Position 4: empty' });

    // Waits for this asynchronous operation to complete.
    await user.click(fourthSlot);
    // Waits for this asynchronous operation to complete.
    await user.keyboard('1');

    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeDisabled();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('starts a new game from the introduction', async () => {
    // Calls apiMock.mockResolvedValue with the supplied values.
    apiMock.mockResolvedValue(activeGame);
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderBoard with the supplied values.
    renderBoard(null);

    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Begin game' }));

    // Calls expect with the supplied values.
    expect(await screen.findByRole('region', { name: 'Submitted guess board' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(apiMock).toHaveBeenCalledWith('/v1/games', expect.objectContaining({ method: 'POST' }));
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('announces initial-load and start failures', async () => {
    // Calls apiMock.mockRejectedValue with the supplied values.
    apiMock.mockRejectedValue(new Error('unavailable'));
    // Calls renderBoard with the supplied values.
    renderBoard();

    // Calls expect with the supplied values.
    expect(await screen.findByRole('alert')).toHaveTextContent(
      // Supplies this item to the surrounding call or collection.
      'The request could not be completed. Please try again.',
      // Closes the expression, call, or declaration started above.
    );

    // Calls cleanup with the supplied values.
    cleanup();
    // Calls render with the supplied values.
    render(
      // Renders the NextIntlClientProvider interface element or component.
      <NextIntlClientProvider locale="en" messages={messages}>
        {/* Renders the GameBoard interface element or component. */}
        <GameBoard title="Code-breaking board" />
        {/* Closes the NextIntlClientProvider interface element. */}
      </NextIntlClientProvider>,
      // Closes the expression, call, or declaration started above.
    );
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Begin game' }));
    // Calls expect with the supplied values.
    expect(await screen.findByRole('alert')).toHaveTextContent(
      // Supplies this item to the surrounding call or collection.
      'The request could not be completed. Please try again.',
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('supports arrow, delete, clear, offline, and board-level submit keys', async () => {
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem('cipherboard:row:game-1', '{invalid json');
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string) => {
      // Checks this condition before running the nested branch.
      if (path.endsWith('/attempts')) throw new Error('submission rejected');
      // Returns this result to the caller and ends the current function.
      return activeGame;
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderBoard with the supplied values.
    renderBoard();
    // Computes and stores firstSlot for subsequent operations.
    const firstSlot = await screen.findByRole('button', { name: 'Position 1: empty' });

    // Calls firstSlot.focus with the supplied values.
    firstSlot.focus();
    // Waits for this asynchronous operation to complete.
    await user.keyboard('{ArrowRight}');
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Position 2: empty' })).toHaveFocus();
    // Waits for this asynchronous operation to complete.
    await user.keyboard('2');
    // Waits for this asynchronous operation to complete.
    await user.keyboard('{ArrowLeft}{Backspace}');
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Position 2: empty' })).toBeVisible();

    // Calls firstSlot.focus with the supplied values.
    firstSlot.focus();
    // Iterates through these values for the nested operation.
    for (const key of ['1', '2', '3', '4']) await user.keyboard(key);
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Clear row' }));
    // Calls expect with the supplied values.
    expect(firstSlot).toHaveFocus();

    // Iterates through these values for the nested operation.
    for (const key of ['1', '2', '3', '4']) await user.keyboard(key);
    // Calls Object.defineProperty with the supplied values.
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
    // Calls fireEvent with the supplied values.
    fireEvent(window, new Event('offline'));
    // Calls expect with the supplied values.
    expect(
      // Waits for this asynchronous operation to complete.
      await screen.findByText('Your unsubmitted row is preserved. Reconnect before submitting.'),
      // Executes this line as the next step in the surrounding logic.
    ).toBeVisible();
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeDisabled();

    // Calls Object.defineProperty with the supplied values.
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    // Calls fireEvent with the supplied values.
    fireEvent(window, new Event('online'));
    // Waits for this asynchronous operation to complete.
    await waitFor(() => expect(screen.getByRole('button', { name: 'Submit guess' })).toBeEnabled());
    // Computes and stores workspace for subsequent operations.
    const workspace = screen.getByRole('region', { name: 'Code-breaking board' });
    // Calls fireEvent.keyDown with the supplied values.
    fireEvent.keyDown(workspace, { key: 'Enter' });
    // Calls expect with the supplied values.
    expect(await screen.findByRole('alert')).toHaveTextContent(
      // Supplies this item to the surrounding call or collection.
      'The request could not be completed. Please try again.',
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('reuses the same idempotency key when an uncertain attempt is retried', async () => {
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string) => {
      // Checks this condition before running the nested branch.
      if (path.endsWith('/attempts')) throw new Error('connection interrupted');
      // Returns this result to the caller and ends the current function.
      return activeGame;
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderBoard with the supplied values.
    renderBoard();
    // Waits for this asynchronous operation to complete.
    await screen.findByRole('button', { name: 'Position 1: empty' });
    // Iterates through these values for the nested operation.
    for (const color of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square']) {
      // Waits for this asynchronous operation to complete.
      await user.click(screen.getByRole('button', { name: new RegExp(`Choose ${color}`) }));
      // Closes the expression, call, or declaration started above.
    }

    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Submit guess' }));
    // Waits for this asynchronous operation to complete.
    await screen.findByRole('alert');
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeDisabled();
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Retry game restore' }));
    // Waits for this asynchronous operation to complete.
    await waitFor(() => expect(screen.getByRole('button', { name: 'Submit guess' })).toBeEnabled());
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Submit guess' }));
    // Waits for this asynchronous operation to complete.
    await waitFor(
      // Continues the surrounding operation with this required value or expression.
      () =>
        // Calls expect with the supplied values.
        expect(
          // Calls apiMock.mock.calls.filter with the supplied values.
          apiMock.mock.calls.filter(([path]) => String(path).endsWith('/attempts')),
          // Supplies this item to the surrounding call or collection.
        ).toHaveLength(2),
      // Closes the expression, call, or declaration started above.
    );

    // Computes and stores attempts for subsequent operations.
    const attempts = apiMock.mock.calls.filter(([path]) => String(path).endsWith('/attempts'));
    // Computes and stores first for subsequent operations.
    const first = JSON.parse(String((attempts[0]?.[1] as RequestInit).body)) as {
      // Defines the idempotencyKey field in the surrounding object or type.
      idempotencyKey: string;
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores second for subsequent operations.
    const second = JSON.parse(String((attempts[1]?.[1] as RequestInit).body)) as {
      // Defines the idempotencyKey field in the surrounding object or type.
      idempotencyKey: string;
      // Closes the expression, call, or declaration started above.
    };
    // Calls expect with the supplied values.
    expect(second.idempotencyKey).toBe(first.idempotencyKey);
    // Calls expect with the supplied values.
    expect(
      // Calls JSON.parse with the supplied values.
      JSON.parse(localStorage.getItem('cipherboard:pending-attempt:game-1') ?? '{}'),
      // Executes this line as the next step in the surrounding logic.
    ).toMatchObject({ idempotencyKey: first.idempotencyKey, guess: ['R', 'B', 'G', 'Y'] });
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('keeps a deterministic duplicate validation failure editable without resyncing', async () => {
    // Computes and stores noDuplicatesGame for subsequent operations.
    const noDuplicatesGame: Game = {
      // Supplies this item to the surrounding call or collection.
      ...activeGame,
      // Defines the config field in the surrounding object or type.
      config: { ...activeGame.config, duplicatesAllowed: false },
      // Closes the expression, call, or declaration started above.
    };
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string) => {
      // Checks this condition before running the nested branch.
      if (path.endsWith('/attempts'))
        // Throws this error to report an invalid or failed operation.
        throw new ApiError(422, {
          // Defines the code field in the surrounding object or type.
          code: 'DUPLICATES_NOT_ALLOWED',
          // Defines the message field in the surrounding object or type.
          message: 'This game does not allow duplicate colours.',
          // Defines the requestId field in the surrounding object or type.
          requestId: 'request-1',
          // Closes the expression, call, or declaration started above.
        });
      // Returns this result to the caller and ends the current function.
      return noDuplicatesGame;
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderBoard with the supplied values.
    renderBoard();
    // Waits for this asynchronous operation to complete.
    await screen.findByRole('button', { name: 'Position 1: empty' });
    // Computes and stores red for subsequent operations.
    const red = screen.getByRole('button', { name: /Choose Red circle/ });
    // Iterates through these values for the nested operation.
    for (let index = 0; index < 4; index += 1) await user.click(red);

    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Submit guess' }));

    // Calls expect with the supplied values.
    expect(await screen.findByRole('alert')).toHaveTextContent(
      // Supplies this item to the surrounding call or collection.
      'This game does not allow repeated pegs. Change the repeated peg and submit again.',
      // Closes the expression, call, or declaration started above.
    );
    // Calls expect with the supplied values.
    expect(screen.queryByRole('button', { name: 'Retry game restore' })).not.toBeInTheDocument();
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeEnabled();
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Position 1: Red circle' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Position 4: Red circle' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(localStorage.getItem('cipherboard:pending-attempt:game-1')).toBeNull();
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Clear row' }));
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeDisabled();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('reconciles an accepted attempt after reconnect without submitting it twice', async () => {
    // Computes and stores progressedGame for subsequent operations.
    const progressedGame: Game = {
      // Supplies this item to the surrounding call or collection.
      ...activeGame,
      // Defines the attempts field in the surrounding object or type.
      attempts: [
        // Begins the nested block or object completed below.
        {
          // Defines the number field in the surrounding object or type.
          number: 1,
          // Defines the guess field in the surrounding object or type.
          guess: ['R', 'B', 'G', 'Y'],
          // Defines the feedback field in the surrounding object or type.
          feedback: { black: 0, white: 2 },
          // Defines the submittedAt field in the surrounding object or type.
          submittedAt: new Date().toISOString(),
          // Closes the expression, call, or declaration started above.
        },
        // Closes the expression, call, or declaration started above.
      ],
      // Defines the attemptsUsed field in the surrounding object or type.
      attemptsUsed: 1,
      // Defines the attemptsRemaining field in the surrounding object or type.
      attemptsRemaining: 9,
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores gameLoads for subsequent operations.
    let gameLoads = 0;
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string) => {
      // Checks this condition before running the nested branch.
      if (path.endsWith('/attempts')) throw new Error('response lost');
      // Checks this condition before running the nested branch.
      if (path === '/v1/games/game-1') {
        // Executes this line as the next step in the surrounding logic.
        gameLoads += 1;
        // Returns this result to the caller and ends the current function.
        return gameLoads === 1 ? activeGame : progressedGame;
        // Closes the expression, call, or declaration started above.
      }
      // Returns this result to the caller and ends the current function.
      return { bestScoreByDifficulty: {} };
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderBoard with the supplied values.
    renderBoard();
    // Waits for this asynchronous operation to complete.
    await screen.findByRole('button', { name: 'Position 1: empty' });
    // Iterates through these values for the nested operation.
    for (const color of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square']) {
      // Waits for this asynchronous operation to complete.
      await user.click(screen.getByRole('button', { name: new RegExp(`Choose ${color}`) }));
      // Closes the expression, call, or declaration started above.
    }
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Submit guess' }));
    // Waits for this asynchronous operation to complete.
    await screen.findByRole('alert');

    // Calls Object.defineProperty with the supplied values.
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
    // Calls fireEvent with the supplied values.
    fireEvent(window, new Event('offline'));
    // Calls Object.defineProperty with the supplied values.
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    // Calls fireEvent with the supplied values.
    fireEvent(window, new Event('online'));

    // Calls expect with the supplied values.
    expect(
      // Waits for this asynchronous operation to complete.
      await screen.findByRole('group', {
        // Defines the name field in the surrounding object or type.
        name: 'Attempt 1: 0 exact-position and 2 correct-colour clues',
        // Closes the expression, call, or declaration started above.
      }),
      // Executes this line as the next step in the surrounding logic.
    ).toBeVisible();
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Position 1: empty' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(localStorage.getItem('cipherboard:pending-attempt:game-1')).toBeNull();
    // Calls expect with the supplied values.
    expect(apiMock.mock.calls.filter(([path]) => String(path).endsWith('/attempts'))).toHaveLength(
      // Supplies this item to the surrounding call or collection.
      1,
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('confirms abandonment and focuses its terminal result', async () => {
    // Computes and stores abandonedGame for subsequent operations.
    const abandonedGame: Game = {
      // Supplies this item to the surrounding call or collection.
      ...activeGame,
      // Defines the status field in the surrounding object or type.
      status: 'abandoned',
      // Defines the completedAt field in the surrounding object or type.
      completedAt: new Date().toISOString(),
      // Defines the score field in the surrounding object or type.
      score: 0,
      // Closes the expression, call, or declaration started above.
    };
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(
      // Continues the surrounding operation with this required value or expression.
      async (path: string) =>
        // Calls path.endsWith with the supplied values.
        path.endsWith('/abandon') ? abandonedGame : activeGame,
      // Closes the expression, call, or declaration started above.
    );
    // Calls vi.spyOn with the supplied values.
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Executes this line as the next step in the surrounding logic.
    const { container } = renderBoard();

    // Waits for this asynchronous operation to complete.
    await screen.findByRole('button', { name: 'Abandon game' });
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Abandon game' }));

    // Calls expect with the supplied values.
    expect(await screen.findByRole('heading', { level: 2, name: 'Game abandoned' })).toBeVisible();
    // Waits for this asynchronous operation to complete.
    await waitFor(() => expect(container.querySelector('.result-panel')).toHaveFocus());
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('starts daily and friend replays explicitly as unranked practice', async () => {
    // Computes and stores practiceGame for subsequent operations.
    const practiceGame: Game = {
      // Supplies this item to the surrounding call or collection.
      ...activeGame,
      // Defines the mode field in the surrounding object or type.
      mode: 'practice',
      // Defines the ranked field in the surrounding object or type.
      ranked: false,
      // Defines the config field in the surrounding object or type.
      config: { ...activeGame.config, ranked: false },
      // Closes the expression, call, or declaration started above.
    };
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string, options?: RequestInit) => {
      // Checks this condition before running the nested branch.
      if (path === '/v1/daily/start' && options?.method === 'POST') return practiceGame;
      // Checks this condition before running the nested branch.
      if (path === '/v1/me/stats') return { bestScoreByDifficulty: {} };
      // Returns this result to the caller and ends the current function.
      return wonGame;
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls render with the supplied values.
    render(
      // Renders the NextIntlClientProvider interface element or component.
      <NextIntlClientProvider locale="en" messages={messages}>
        {/* Renders the GameBoard interface element or component. */}
        <GameBoard
          /* Provides the title value to the surrounding call or element. */
          title="Daily challenge"
          /* Provides the initialGameId value to the surrounding call or element. */
          initialGameId="game-1"
          /* Provides the startEndpoint value to the surrounding call or element. */
          startEndpoint="/v1/daily/start"
          /* Provides the replayBody value to the surrounding call or element. */
          replayBody={{ practice: true }}
          /* Provides the replayLabel value to the surrounding call or element. */
          replayLabel="Play again unranked"
          /* Executes this line as the next step in the surrounding logic. */
        />
        {/* Closes the NextIntlClientProvider interface element. */}
      </NextIntlClientProvider>,
      // Closes the expression, call, or declaration started above.
    );

    // Waits for this asynchronous operation to complete.
    await user.click(await screen.findByRole('button', { name: 'Play again unranked' }));

    // Calls expect with the supplied values.
    expect(apiMock).toHaveBeenCalledWith('/v1/daily/start', {
      // Defines the method field in the surrounding object or type.
      method: 'POST',
      // Defines the body field in the surrounding object or type.
      body: JSON.stringify({ practice: true }),
      // Closes the expression, call, or declaration started above.
    });
    // Calls expect with the supplied values.
    expect(await screen.findByText('Practice')).toBeVisible();
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('restores the active daily game and its unsubmitted row after a remount', async () => {
    // Computes and stores dailyGame for subsequent operations.
    const dailyGame: Game = { ...activeGame, id: 'daily-game-1', mode: 'daily' };
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem('cipherboard:daily:daily-challenge-1:active-game', dailyGame.id);
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem(`cipherboard:row:${dailyGame.id}`, JSON.stringify(['R', 'B', 'G', 'Y']));
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string) => {
      // Checks this condition before running the nested branch.
      if (path === `/v1/games/${dailyGame.id}`) return dailyGame;
      // Returns this result to the caller and ends the current function.
      return { bestScoreByDifficulty: {} };
      // Closes the expression, call, or declaration started above.
    });

    // Calls render with the supplied values.
    render(
      // Renders the NextIntlClientProvider interface element or component.
      <NextIntlClientProvider locale="en" messages={messages}>
        {/* Renders the GameBoard interface element or component. */}
        <GameBoard
          /* Provides the title value to the surrounding call or element. */
          title="Daily challenge"
          /* Provides the startEndpoint value to the surrounding call or element. */
          startEndpoint="/v1/daily/start"
          /* Provides the startBody value to the surrounding call or element. */
          startBody={{ practice: false }}
          /* Provides the dailyChallengeId value to the surrounding call or element. */
          dailyChallengeId="daily-challenge-1"
          /* Executes this line as the next step in the surrounding logic. */
        />
        {/* Closes the NextIntlClientProvider interface element. */}
      </NextIntlClientProvider>,
      // Closes the expression, call, or declaration started above.
    );

    // Calls expect with the supplied values.
    expect(await screen.findByRole('button', { name: 'Position 4: Yellow square' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(screen.getByRole('button', { name: 'Submit guess' })).toBeEnabled();
    // Calls expect with the supplied values.
    expect(apiMock).toHaveBeenCalledWith(`/v1/games/${dailyGame.id}`);
    // Calls expect with the supplied values.
    expect(
      // Calls apiMock.mock.calls.some with the supplied values.
      apiMock.mock.calls.some(
        // Supplies this item to the surrounding call or collection.
        ([path, options]) => path === '/v1/daily/start' && options?.method === 'POST',
        // Closes the expression, call, or declaration started above.
      ),
      // Executes this line as the next step in the surrounding logic.
    ).toBe(false);
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('clears an inaccessible stored daily game and returns to a startable state', async () => {
    // Computes and stores storageKey for subsequent operations.
    const storageKey = 'cipherboard:daily:daily-challenge-1:active-game';
    // Calls localStorage.setItem with the supplied values.
    localStorage.setItem(storageKey, 'stale-game-id');
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string) => {
      // Checks this condition before running the nested branch.
      if (path === '/v1/games/stale-game-id') throw new Error('not found');
      // Checks this condition before running the nested branch.
      if (path === '/v1/daily/start') return { ...activeGame, id: 'daily-game-2', mode: 'daily' };
      // Returns this result to the caller and ends the current function.
      return { bestScoreByDifficulty: {} };
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();

    // Calls render with the supplied values.
    render(
      // Renders the NextIntlClientProvider interface element or component.
      <NextIntlClientProvider locale="en" messages={messages}>
        {/* Renders the GameBoard interface element or component. */}
        <GameBoard
          /* Provides the title value to the surrounding call or element. */
          title="Daily challenge"
          /* Provides the startEndpoint value to the surrounding call or element. */
          startEndpoint="/v1/daily/start"
          /* Provides the startBody value to the surrounding call or element. */
          startBody={{ practice: false }}
          /* Provides the dailyChallengeId value to the surrounding call or element. */
          dailyChallengeId="daily-challenge-1"
          /* Executes this line as the next step in the surrounding logic. */
        />
        {/* Closes the NextIntlClientProvider interface element. */}
      </NextIntlClientProvider>,
      // Closes the expression, call, or declaration started above.
    );

    // Computes and stores start for subsequent operations.
    const start = await screen.findByRole('button', { name: 'Begin game' });
    // Calls expect with the supplied values.
    expect(start).toBeEnabled();
    // Calls expect with the supplied values.
    expect(localStorage.getItem(storageKey)).toBeNull();
    // Waits for this asynchronous operation to complete.
    await user.click(start);
    // Calls expect with the supplied values.
    expect(await screen.findByRole('region', { name: 'Submitted guess board' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(localStorage.getItem(storageKey)).toBe('daily-game-2');
    // Closes the expression, call, or declaration started above.
  });

  // Calls it with the supplied values.
  it('shows only achievements earned during the just-completed game', async () => {
    // Computes and stores statsCalls for subsequent operations.
    let statsCalls = 0;
    // Calls apiMock.mockImplementation with the supplied values.
    apiMock.mockImplementation(async (path: string) => {
      // Checks this condition before running the nested branch.
      if (path === '/v1/me/stats') {
        // Executes this line as the next step in the surrounding logic.
        statsCalls += 1;
        // Returns this result to the caller and ends the current function.
        return {
          // Defines the bestScoreByDifficulty field in the surrounding object or type.
          bestScoreByDifficulty: { normal: 1000 },
          // Defines the achievements field in the surrounding object or type.
          achievements: statsCalls === 1 ? ['first_break'] : ['first_break', 'one_shot'],
          // Closes the expression, call, or declaration started above.
        };
        // Closes the expression, call, or declaration started above.
      }
      // Checks this condition before running the nested branch.
      if (path.startsWith('/v1/leaderboards')) return { currentUserRank: 7 };
      // Checks this condition before running the nested branch.
      if (path.endsWith('/attempts')) return wonGame;
      // Returns this result to the caller and ends the current function.
      return activeGame;
      // Closes the expression, call, or declaration started above.
    });
    // Computes and stores user for subsequent operations.
    const user = userEvent.setup();
    // Calls renderBoard with the supplied values.
    renderBoard();
    // Waits for this asynchronous operation to complete.
    await screen.findByRole('button', { name: 'Position 1: empty' });
    // Waits for this asynchronous operation to complete.
    await waitFor(() => expect(statsCalls).toBe(1));

    // Iterates through these values for the nested operation.
    for (const color of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square']) {
      // Waits for this asynchronous operation to complete.
      await user.click(screen.getByRole('button', { name: new RegExp(`Choose ${color}`) }));
      // Closes the expression, call, or declaration started above.
    }
    // Waits for this asynchronous operation to complete.
    await user.click(screen.getByRole('button', { name: 'Submit guess' }));

    // Calls expect with the supplied values.
    expect(await screen.findByRole('heading', { name: 'Achievements earned' })).toBeVisible();
    // Calls expect with the supplied values.
    expect(screen.getByText('One Shot')).toBeVisible();
    // Calls expect with the supplied values.
    expect(screen.queryByText('First break')).not.toBeInTheDocument();
    // Calls expect with the supplied values.
    expect(screen.getByText('Leaderboard position: 7')).toBeVisible();
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
});
