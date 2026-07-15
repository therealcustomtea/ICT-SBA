import { expect, test } from '@playwright/test';
import {
  apiOrigin,
  apiRequest,
  captureSession,
  chooseDuelGuess,
  chooseGuess,
  createKnownGame,
  enumerateMastermindCandidates,
  expectActiveSecretOmitted,
  narrowMastermindCandidates,
  type GameResponse,
  type RoomResponse,
  submitGuess,
} from './helpers';

test.describe('real product flows', () => {
  test.describe.configure({ mode: 'serial' });
  test.beforeEach(async ({ isMobile }) => {
    test.skip(Boolean(isMobile), 'The desktop project owns these multi-step product flows.');
  });

  test('anonymous guest launches Easy, Hard, Expert, and custom games', async ({ page }) => {
    test.setTimeout(60_000);
    const { token, profile } = await captureSession(page);
    expect(profile.isAnonymous).toBe(true);

    const presets = [
      {
        value: 'easy',
        label: 'Easy',
        expected: { colours: 5, codeLength: 4, maxAttempts: 12, duplicatesAllowed: false },
      },
      {
        value: 'hard',
        label: 'Hard',
        expected: { colours: 8, codeLength: 5, maxAttempts: 8, duplicatesAllowed: true },
      },
      {
        value: 'expert',
        label: 'Expert',
        expected: { colours: 10, codeLength: 6, maxAttempts: 8, duplicatesAllowed: true },
      },
    ] as const;

    for (const preset of presets) {
      await page.goto('/en/play');
      await page.getByText(preset.label, { exact: true }).click();
      const responsePromise = page.waitForResponse(
        (response) =>
          response.url() === `${apiOrigin}/v1/games` && response.request().method() === 'POST',
      );
      await page.getByRole('button', { name: 'Start game', exact: true }).click();
      const game = await expectActiveSecretOmitted(await responsePromise);
      expect(game.difficulty).toBe(preset.value);
      expect(game.config.colours).toHaveLength(preset.expected.colours);
      expect(game.config.codeLength).toBe(preset.expected.codeLength);
      expect(game.config.maxAttempts).toBe(preset.expected.maxAttempts);
      expect(game.config.duplicatesAllowed).toBe(preset.expected.duplicatesAllowed);
      await expect(page).toHaveURL(new RegExp(`/en/play/${game.id}$`));

      const abandon = await apiRequest(page, token, `/v1/games/${game.id}/abandon`, {
        method: 'POST',
      });
      expect(abandon.ok()).toBe(true);
    }

    await page.goto('/en/play');
    await page.getByText('Custom', { exact: true }).click();
    await page.locator('input[name="colour-count"]').fill('7');
    await page.locator('input[name="code-length"]').fill('5');
    await page.locator('input[name="maximum-attempts"]').fill('3');
    const customResponse = page.waitForResponse(
      (response) =>
        response.url() === `${apiOrigin}/v1/games` && response.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Start game', exact: true }).click();
    const custom = await expectActiveSecretOmitted(await customResponse);
    expect(custom.difficulty).toBeNull();
    expect(custom.ranked).toBe(false);
    expect(custom.config).toMatchObject({
      codeLength: 5,
      maxAttempts: 3,
      duplicatesAllowed: true,
    });
    expect(custom.config.colours).toHaveLength(7);
  });

  test('human Code Maker game rejects duplicates without consuming a turn, restores, and wins on the final attempt', async ({
    context,
    page,
  }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
    });
    const { token } = await captureSession(page);
    await page.evaluate(() => {
      localStorage.setItem(
        'cipherboard:preferences',
        JSON.stringify({
          theme: 'light',
          pegStyle: 'patterns',
          reducedMotion: false,
          sound: false,
          analytics: true,
        }),
      );
    });
    const analyticsBodies: string[] = [];
    page.on('request', (request) => {
      if (request.url() === `${apiOrigin}/v1/analytics/events` && request.postData())
        analyticsBodies.push(request.postData()!);
    });

    await page.goto('/en/play');
    await page.getByText('Pass-and-play Code Maker', { exact: true }).click();
    await page.getByText('Custom', { exact: true }).click();
    await page.locator('input[name="maximum-attempts"]').fill('2');
    await page.getByText('Allow duplicate colours', { exact: true }).click();
    for (const name of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square'])
      await page.getByRole('button', { name, exact: true }).click();

    await page.getByRole('button', { name: 'Confirm and conceal code', exact: true }).click();
    await expect(page.getByText('Code concealed', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Red circle', exact: true })).toHaveCount(0);

    const creationResponse = page.waitForResponse(
      (response) =>
        response.url() === `${apiOrigin}/v1/games` && response.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Begin Code Breaker turn', exact: true }).click();
    const secret = ['R', 'B', 'G', 'Y'];
    const game = await expectActiveSecretOmitted(await creationResponse, secret);
    await expect(page).toHaveURL(new RegExp(`/en/play/${game.id}$`));
    await expect(page.getByText('Revealed code', { exact: true })).toHaveCount(0);
    const browserStorage = await page.evaluate(() => JSON.stringify({ ...localStorage }));
    expect(browserStorage).not.toContain(JSON.stringify(secret));

    await chooseGuess(page, ['R', 'R', 'R', 'R']);
    const invalidResponse = await submitGuess(page);
    expect(invalidResponse.status()).toBe(422);
    await expect(page.locator('.inline-error[role="alert"]')).toContainText(
      'does not allow repeated pegs',
    );
    const unchanged = await apiRequest(page, token, `/v1/games/${game.id}`);
    expect((await unchanged.json()).attemptsUsed).toBe(0);
    await expect(page.getByRole('button', { name: 'Retry game restore', exact: true })).toHaveCount(
      0,
    );
    await page.getByRole('button', { name: 'Clear row', exact: true }).click();

    await chooseGuess(page, ['W', 'R', 'B', 'G']);
    const firstAttempt = await submitGuess(page);
    const afterFirst = await expectActiveSecretOmitted(firstAttempt, secret);
    expect(afterFirst.attemptsUsed).toBe(1);
    await expect(page.getByRole('group', { name: /^Attempt 1:/ })).toBeVisible();

    await page.reload();
    await expect(page.getByRole('group', { name: /^Attempt 1:/ })).toBeVisible();
    await expect(page.getByText('Revealed code', { exact: true })).toHaveCount(0);

    await chooseGuess(page, secret);
    const finalAttemptResponse = await submitGuess(page);
    expect(finalAttemptResponse.ok()).toBe(true);
    const completed = (await finalAttemptResponse.json()) as GameResponse;
    expect(completed.status).toBe('won');
    expect(completed.attemptsUsed).toBe(2);
    expect(completed.secret).toEqual(secret);
    await expect(page.getByRole('heading', { name: 'Code broken', exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Share result', exact: true }).click();
    const shared = await page.evaluate(() => navigator.clipboard.readText());
    expect(shared).toContain('Solved in 2/2');
    expect(shared).not.toContain(JSON.stringify(secret));
    expect(shared).not.toContain(secret.join(''));

    await expect.poll(() => analyticsBodies.length).toBeGreaterThan(0);
    for (const body of analyticsBodies) {
      const payload = JSON.parse(body) as Record<string, unknown>;
      expect(body).not.toContain(JSON.stringify(secret));
      expect(payload).not.toHaveProperty('secret');
      expect(payload).not.toHaveProperty('guess');
    }
  });

  test('a final failed attempt ends the game as a loss and remains terminal after refresh', async ({
    page,
  }) => {
    const { token } = await captureSession(page);
    const game = await createKnownGame(page, token, { maxAttempts: 1 });
    await page.goto(`/en/play/${game.id}`);
    await expect(page.getByRole('heading', { name: 'Code-breaking board' })).toBeVisible();
    await chooseGuess(page, ['W', 'R', 'B', 'G']);
    const response = await submitGuess(page);
    const lost = (await response.json()) as GameResponse;
    expect(lost.status).toBe('lost');
    expect(lost.attemptsRemaining).toBe(0);
    await expect(page.getByRole('heading', { name: 'The code held', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Submit guess', exact: true })).toHaveCount(0);
    await page.reload();
    await expect(page.getByRole('heading', { name: 'The code held', exact: true })).toBeVisible();
  });

  test('daily play supports keyboard input, Traditional Chinese, dark mode, reduced motion, and denies guest admin access', async ({
    page,
  }) => {
    const { token } = await captureSession(page);
    await page.goto('/en/daily');
    await expect(page.getByRole('heading', { name: 'Daily challenge', exact: true })).toBeVisible();
    const startResponse = page.waitForResponse(
      (response) =>
        response.url() === `${apiOrigin}/v1/daily/start` && response.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Begin game', exact: true }).click();
    const game = await expectActiveSecretOmitted(await startResponse);

    const firstSlot = page.getByRole('button', { name: /^Position 1:/ });
    await firstSlot.focus();
    for (const key of ['1', '2', '3', '4']) await page.keyboard.press(key);
    await expect(page.getByRole('button', { name: /Position 4: Yellow square/ })).toBeVisible();
    await page.getByRole('button', { name: 'Submit guess', exact: true }).focus();
    await expect(page.getByRole('button', { name: 'Submit guess', exact: true })).toBeFocused();

    const restoreResponse = page.waitForResponse(
      (response) =>
        response.url() === `${apiOrigin}/v1/games/${game.id}` &&
        response.request().method() === 'GET',
    );
    await page.getByRole('link', { name: 'Switch language' }).click();
    await expect(page).toHaveURL(new RegExp(`/zh-Hant/daily$`));
    await expect(page.locator('html')).toHaveAttribute('lang', 'zh-Hant');
    await expect(page.getByRole('heading', { name: '每日挑戰', exact: true })).toBeVisible();
    expect((await (await restoreResponse).json()).id).toBe(game.id);
    await expect(page.getByRole('button', { name: '開始遊戲', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: '提交猜測', exact: true })).toBeEnabled();

    await page.goto('/en/settings');
    await page.locator('select[name="theme"]').selectOption('dark');
    await page.getByText('Reduce motion', { exact: true }).click();
    await page.getByRole('button', { name: 'Save changes', exact: true }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(page.locator('html')).toHaveAttribute('data-reduce-motion', 'true');
    const transitionDuration = await page
      .getByRole('button', { name: 'Use light appearance' })
      .evaluate((element) => getComputedStyle(element).transitionDuration);
    expect(transitionDuration.split(',').every((value) => Number.parseFloat(value) <= 0.001)).toBe(
      true,
    );

    const adminResponse = await apiRequest(page, token, '/v1/admin/summary');
    expect(adminResponse.status()).toBe(403);
    expect((await adminResponse.json()).code).toBe('ADMIN_REQUIRED');
    await page.goto('/en/admin');
    await expect(page.locator('.state-panel[role="alert"]')).toContainText(
      'You do not have permission to access administration.',
    );

    const abandon = await apiRequest(page, token, `/v1/games/${game.id}/abandon`, {
      method: 'POST',
    });
    expect(abandon.ok()).toBe(true);
  });

  test('manual friend challenge crosses guest browsers and records a verified win', async ({
    browser,
    page,
  }) => {
    const { token: creatorToken } = await captureSession(page);
    await page.goto('/en/challenges/new');
    await page.locator('input[name="challenge-title"]').fill('E2E private challenge');
    await page.getByText('Easy', { exact: true }).click();
    await page.getByText('Enter the code myself', { exact: true }).click();
    const secret = ['R', 'B', 'G', 'Y'];
    for (const name of ['Red circle', 'Blue diamond', 'Green triangle', 'Yellow square'])
      await page.getByRole('button', { name, exact: true }).click();
    const creationResponse = page.waitForResponse(
      (response) =>
        response.url() === `${apiOrigin}/v1/challenges` && response.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Create challenge', exact: true }).click();
    const rawChallenge = await (await creationResponse).text();
    const challenge = JSON.parse(rawChallenge) as { id: string; shareCode: string };
    expect(rawChallenge).not.toContain(JSON.stringify(secret));
    expect(challenge.shareCode).toMatch(/^[A-Za-z0-9_-]{20,}$/);
    const shareUrl = await page.locator('input[name="share-url"]').inputValue();
    expect(new URL(shareUrl).search).toBe('');
    expect(shareUrl).not.toContain(secret.join(''));

    const playerContext = await browser.newContext();
    const playerPage = await playerContext.newPage();
    try {
      await captureSession(playerPage);
      await playerPage.goto(`/en/challenges/${challenge.shareCode}`);
      await expect(
        playerPage.getByRole('heading', {
          level: 1,
          name: 'E2E private challenge',
          exact: true,
        }),
      ).toBeVisible();
      const startResponse = playerPage.waitForResponse(
        (response) =>
          response.url() === `${apiOrigin}/v1/challenges/${challenge.shareCode}/start` &&
          response.request().method() === 'POST',
      );
      await playerPage.getByRole('button', { name: 'Begin game', exact: true }).click();
      await expectActiveSecretOmitted(await startResponse, secret);
      await chooseGuess(playerPage, secret);
      const winResponse = await submitGuess(playerPage);
      expect(((await winResponse.json()) as GameResponse).status).toBe('won');
      await expect(
        playerPage.getByRole('heading', { name: 'Code broken', exact: true }),
      ).toBeVisible();

      await expect
        .poll(async () => {
          const results = await apiRequest(
            page,
            creatorToken,
            `/v1/challenges/${challenge.id}/results?page=1&page_size=10`,
          );
          return ((await results.json()) as { completedCount: number }).completedCount;
        })
        .toBe(1);
    } finally {
      await playerContext.close();
    }
  });

  test('two anonymous browsers solve a duel, reconcile its terminal event, and restore persisted state', async ({
    browser,
    page,
  }) => {
    test.setTimeout(90_000);
    const creatorSession = await captureSession(page);
    const opponentContext = await browser.newContext();
    const opponent = await opponentContext.newPage();
    try {
      const opponentSession = await captureSession(opponent);
      await page.goto('/en/rooms');
      await page.getByText('Easy', { exact: true }).click();
      const createResponse = page.waitForResponse(
        (response) =>
          response.url() === `${apiOrigin}/v1/rooms` && response.request().method() === 'POST',
      );
      await page.getByRole('button', { name: 'Create room', exact: true }).click();
      const created = (await (await createResponse).json()) as RoomResponse;
      expect(created.status).toBe('waiting');
      expect(created.roomCode).toMatch(/^[A-Za-z0-9_-]{20,64}$/);
      expect(created.config).toMatchObject({
        codeLength: 4,
        maxAttempts: 12,
        duplicatesAllowed: false,
      });
      expect(created.config.colours).toHaveLength(5);
      await expect(page).toHaveURL(new RegExp(`/en/rooms/${created.id}$`));

      await opponent.goto(`/en/rooms?code=${created.roomCode}`);
      const joinResponse = opponent.waitForResponse(
        (response) =>
          response.url().endsWith(`/v1/rooms/${created.roomCode}/join`) &&
          response.request().method() === 'POST',
      );
      await opponent.getByRole('button', { name: 'Join room', exact: true }).click();
      const joined = (await (await joinResponse).json()) as RoomResponse;
      expect(joined.members).toHaveLength(2);
      await expect(page.locator('.member-list li')).toHaveCount(2, { timeout: 10_000 });

      await page.getByRole('button', { name: 'I’m ready', exact: true }).click();
      const opponentReadyResponse = opponent.waitForResponse(
        (response) =>
          response.url().endsWith(`/v1/rooms/${created.id}/ready`) &&
          response.request().method() === 'POST',
      );
      await opponent.getByRole('button', { name: 'I’m ready', exact: true }).click();
      expect(((await (await opponentReadyResponse).json()) as RoomResponse).status).toBe('active');

      await expect(page.getByRole('link', { name: 'Start duel', exact: true })).toBeVisible({
        timeout: 10_000,
      });
      await expect(opponent.getByRole('link', { name: 'Start duel', exact: true })).toBeVisible();
      let creatorSockets = 0;
      page.on('websocket', () => {
        creatorSockets += 1;
      });
      await Promise.all([
        page.getByRole('link', { name: 'Start duel', exact: true }).click(),
        opponent.getByRole('link', { name: 'Start duel', exact: true }).click(),
      ]);
      await expect(page.locator('.duel-layout')).toBeVisible({ timeout: 15_000 });
      await expect(opponent.locator('.duel-layout')).toBeVisible({ timeout: 15_000 });

      // Reconnect before guessing so state restoration never depends on whether a random guess wins.
      await page.reload();
      await expect(page.locator('.duel-layout')).toBeVisible({ timeout: 15_000 });
      await expect(page.locator('.duel-layout .attempt-row')).toHaveCount(0);
      await expect.poll(() => creatorSockets).toBeGreaterThanOrEqual(2);

      const creatorRoomResponse = await apiRequest(
        page,
        creatorSession.token,
        `/v1/rooms/${created.id}`,
      );
      const opponentRoomResponse = await apiRequest(
        opponent,
        opponentSession.token,
        `/v1/rooms/${created.id}`,
      );
      const creatorRoom = (await creatorRoomResponse.json()) as RoomResponse;
      const opponentRoom = (await opponentRoomResponse.json()) as RoomResponse;
      const creatorGameId = creatorRoom.members.find(
        (member) => member.userId === creatorSession.profile.id,
      )?.gameId;
      const opponentGameId = opponentRoom.members.find(
        (member) => member.userId === opponentSession.profile.id,
      )?.gameId;
      expect(creatorGameId).toBeTruthy();
      expect(opponentGameId).toBeTruthy();

      // Easy has 5P4 = 120 candidates. Selecting the first consistent candidate has a
      // six-attempt worst case, comfortably inside Easy's twelve server-authoritative turns.
      let candidates = enumerateMastermindCandidates(
        created.config.colours,
        created.config.codeLength,
        created.config.duplicatesAllowed,
      );
      expect(candidates).toHaveLength(120);
      let creatorGame: GameResponse | null = null;
      let opponentGame: GameResponse | null = null;

      for (let attemptNumber = 1; attemptNumber <= 6; attemptNumber += 1) {
        const guess = candidates[0];
        expect(guess).toHaveLength(created.config.codeLength);
        await Promise.all([chooseDuelGuess(page, guess!), chooseDuelGuess(opponent, guess!)]);
        await Promise.all([
          expect(page.getByRole('button', { name: 'Submit guess', exact: true })).toBeEnabled(),
          expect(opponent.getByRole('button', { name: 'Submit guess', exact: true })).toBeEnabled(),
        ]);
        await Promise.all([
          page.getByRole('button', { name: 'Submit guess', exact: true }).dispatchEvent('click'),
          opponent
            .getByRole('button', { name: 'Submit guess', exact: true })
            .dispatchEvent('click'),
        ]);

        await expect
          .poll(
            async () => {
              const [creatorResult, opponentResult] = await Promise.all([
                apiRequest(page, creatorSession.token, `/v1/games/${creatorGameId}`),
                apiRequest(opponent, opponentSession.token, `/v1/games/${opponentGameId}`),
              ]);
              creatorGame = (await creatorResult.json()) as GameResponse;
              opponentGame = (await opponentResult.json()) as GameResponse;
              return [creatorGame, opponentGame].every(
                (game) => game.attemptsUsed >= attemptNumber || game.status !== 'active',
              );
            },
            { timeout: 10_000 },
          )
          .toBe(true);

        if (creatorGame!.status !== 'active' || opponentGame!.status !== 'active') break;
        expect(creatorGame!.attemptsUsed).toBe(attemptNumber);
        expect(opponentGame!.attemptsUsed).toBe(attemptNumber);
        expect(opponentGame!.attempts.at(-1)?.feedback).toEqual(
          creatorGame!.attempts.at(-1)?.feedback,
        );
        await Promise.all([
          expect(page.locator('.duel-layout .attempt-row')).toHaveCount(attemptNumber),
          expect(opponent.locator('.duel-layout .attempt-row')).toHaveCount(attemptNumber),
        ]);
        candidates = narrowMastermindCandidates(
          candidates,
          guess!,
          creatorGame!.attempts.at(-1)!.feedback,
        );
        expect(candidates.length).toBeGreaterThan(0);
      }

      expect(creatorGame).not.toBeNull();
      expect(opponentGame).not.toBeNull();
      expect([creatorGame!.status, opponentGame!.status]).toContain('won');

      let finalCreatorRoom: RoomResponse | null = null;
      let finalOpponentRoom: RoomResponse | null = null;
      await expect
        .poll(
          async () => {
            const [creatorResult, opponentResult] = await Promise.all([
              apiRequest(page, creatorSession.token, `/v1/rooms/${created.id}`),
              apiRequest(opponent, opponentSession.token, `/v1/rooms/${created.id}`),
            ]);
            finalCreatorRoom = (await creatorResult.json()) as RoomResponse;
            finalOpponentRoom = (await opponentResult.json()) as RoomResponse;
            return [finalCreatorRoom.status, finalOpponentRoom.status];
          },
          { timeout: 10_000 },
        )
        .toEqual(['completed', 'completed']);

      expect(finalOpponentRoom).toMatchObject({
        status: finalCreatorRoom!.status,
        winnerId: finalCreatorRoom!.winnerId,
        isTie: finalCreatorRoom!.isTie,
      });
      expect(finalCreatorRoom!.members.every((member) => member.completed)).toBe(true);
      expect(finalOpponentRoom!.members.every((member) => member.completed)).toBe(true);

      const [persistedCreatorResponse, persistedOpponentResponse] = await Promise.all([
        apiRequest(page, creatorSession.token, `/v1/games/${creatorGameId}`),
        apiRequest(opponent, opponentSession.token, `/v1/games/${opponentGameId}`),
      ]);
      const persistedCreator = (await persistedCreatorResponse.json()) as GameResponse;
      const persistedOpponent = (await persistedOpponentResponse.json()) as GameResponse;
      expect(['won', 'lost']).toContain(persistedCreator.status);
      expect(['won', 'lost']).toContain(persistedOpponent.status);

      if (finalCreatorRoom!.isTie) {
        expect(finalCreatorRoom!.winnerId).toBeNull();
        expect([persistedCreator.status, persistedOpponent.status]).toEqual(['won', 'won']);
      } else {
        expect([creatorSession.profile.id, opponentSession.profile.id]).toContain(
          finalCreatorRoom!.winnerId,
        );
        expect(persistedCreator.status).toBe(
          finalCreatorRoom!.winnerId === creatorSession.profile.id ? 'won' : 'lost',
        );
        expect(persistedOpponent.status).toBe(
          finalCreatorRoom!.winnerId === opponentSession.profile.id ? 'won' : 'lost',
        );
      }

      const creatorResult = finalCreatorRoom!.isTie
        ? 'The duel ended in a tie'
        : finalCreatorRoom!.winnerId === creatorSession.profile.id
          ? 'You won the duel'
          : 'Your opponent won the duel';
      const opponentResult = finalCreatorRoom!.isTie
        ? 'The duel ended in a tie'
        : finalCreatorRoom!.winnerId === opponentSession.profile.id
          ? 'You won the duel'
          : 'Your opponent won the duel';
      await Promise.all([
        expect(page.getByRole('heading', { name: creatorResult, exact: true })).toBeVisible({
          timeout: 10_000,
        }),
        expect(opponent.getByRole('heading', { name: opponentResult, exact: true })).toBeVisible({
          timeout: 10_000,
        }),
      ]);

      await Promise.all([page.reload(), opponent.reload()]);
      await Promise.all([
        expect(page.getByRole('heading', { name: creatorResult, exact: true })).toBeVisible({
          timeout: 15_000,
        }),
        expect(opponent.getByRole('heading', { name: opponentResult, exact: true })).toBeVisible({
          timeout: 15_000,
        }),
      ]);
      await expect(page.locator('.duel-layout .attempt-row')).toHaveCount(
        persistedCreator.attemptsUsed,
      );
      await expect(opponent.locator('.duel-layout .attempt-row')).toHaveCount(
        persistedOpponent.attemptsUsed,
      );
    } finally {
      await opponentContext.close();
    }
  });
});
