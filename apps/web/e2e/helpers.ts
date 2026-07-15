import { expect, type APIResponse, type Page, type Response } from '@playwright/test';

export const apiOrigin = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://127.0.0.1:8000';

export type ProfileResponse = {
  id: string;
  displayName: string | null;
  isAnonymous: boolean;
  publicLeaderboards: boolean;
  createdAt: string;
};

export type GameResponse = {
  id: string;
  mode: string;
  status: string;
  difficulty: string | null;
  config: {
    colours: string[];
    codeLength: number;
    maxAttempts: number;
    duplicatesAllowed: boolean;
    codeMaker: string;
    visibility: string;
    ranked: boolean;
    timeBonusCap: number;
  };
  attempts: Array<{
    number: number;
    guess: string[];
    feedback: { black: number; white: number };
  }>;
  attemptsUsed: number;
  maxAttempts: number;
  attemptsRemaining: number;
  secret?: string[] | null;
  ranked: boolean;
};

export type RoomResponse = {
  id: string;
  roomCode?: string | null;
  status: string;
  config: GameResponse['config'];
  members: Array<{
    userId: string;
    connected: boolean;
    ready: boolean;
    attemptsUsed: number;
    completed: boolean;
    gameId: string | null;
  }>;
  winnerId: string | null;
  isTie: boolean;
  expiresAt: string;
  eventSequence: number;
};

export type MastermindFeedback = { black: number; white: number };

export async function captureSession(
  page: Page,
  path = '/en/profile',
): Promise<{ token: string; profile: ProfileResponse }> {
  const profileResponse = page.waitForResponse(
    (response) =>
      response.url() === `${apiOrigin}/v1/me/profile` && response.request().method() === 'GET',
  );
  await page.goto(path);
  const response = await profileResponse;
  const authorization = await response.request().headerValue('authorization');
  expect(authorization).toMatch(/^Bearer \S+$/);
  if (!response.ok()) {
    const token = authorization!.slice('Bearer '.length);
    const [encodedHeader = '', encodedClaims = ''] = token.split('.');
    const header = JSON.parse(Buffer.from(encodedHeader, 'base64url').toString('utf8')) as {
      alg?: string;
    };
    const claims = JSON.parse(Buffer.from(encodedClaims, 'base64url').toString('utf8')) as {
      aud?: string;
      iat?: number;
      iss?: string;
    };
    const body = (await response.json()) as { code?: string };
    throw new Error(
      `Profile bootstrap failed (${response.status()} ${body.code ?? 'UNKNOWN'}; ` +
        `alg=${header.alg ?? 'unknown'}; iss=${claims.iss ?? 'unknown'}; ` +
        `aud=${claims.aud ?? 'unknown'}; clockDelta=${(claims.iat ?? 0) - Math.floor(Date.now() / 1000)}s).`,
    );
  }
  return {
    token: authorization!.slice('Bearer '.length),
    profile: (await response.json()) as ProfileResponse,
  };
}

export async function apiRequest(
  page: Page,
  token: string,
  path: string,
  options: { method?: string; body?: unknown } = {},
): Promise<APIResponse> {
  return page.request.fetch(`${apiOrigin}${path}`, {
    method: options.method ?? 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
      ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
    data: options.body,
  });
}

export async function expectActiveSecretOmitted(
  response: APIResponse | Response,
  knownSecret?: string[],
): Promise<GameResponse> {
  expect(response.ok()).toBe(true);
  const raw = await response.text();
  const game = JSON.parse(raw) as GameResponse;
  expect(game.status).toBe('active');
  expect(game.secret ?? null).toBeNull();
  if (knownSecret) {
    expect(raw).not.toContain(JSON.stringify(knownSecret));
    expect(raw).not.toContain(knownSecret.join(''));
  }
  return game;
}

export async function createKnownGame(
  page: Page,
  token: string,
  {
    secret = ['R', 'B', 'G', 'Y'],
    maxAttempts = 2,
    duplicatesAllowed = false,
  }: {
    secret?: string[];
    maxAttempts?: number;
    duplicatesAllowed?: boolean;
  } = {},
): Promise<GameResponse> {
  const colours = ['R', 'B', 'G', 'Y', 'W'];
  const response = await apiRequest(page, token, '/v1/games', {
    method: 'POST',
    body: {
      mode: 'pass_and_play',
      config: {
        colours,
        codeLength: secret.length,
        maxAttempts,
        duplicatesAllowed,
        codeMaker: 'human',
        visibility: 'private',
        ranked: false,
        timeBonusCap: 300,
      },
      secret,
      idempotencyKey: crypto.randomUUID(),
    },
  });
  return expectActiveSecretOmitted(response, secret);
}

export async function chooseGuess(page: Page, guess: string[]): Promise<void> {
  for (const colour of guess) {
    await page.locator(`.game-workspace .palette .peg-${colour}`).click();
  }
}

export async function chooseDuelGuess(page: Page, guess: string[]): Promise<void> {
  for (const colour of guess) {
    await page.locator(`.duel-layout .palette .peg-${colour}`).click();
  }
}

export function enumerateMastermindCandidates(
  colours: string[],
  codeLength: number,
  duplicatesAllowed: boolean,
): string[][] {
  const candidates: string[][] = [];
  const append = (prefix: string[]) => {
    if (prefix.length === codeLength) {
      candidates.push(prefix);
      return;
    }
    for (const colour of colours) {
      if (duplicatesAllowed || !prefix.includes(colour)) append([...prefix, colour]);
    }
  };
  append([]);
  return candidates;
}

export function scoreMastermindGuess(secret: string[], guess: string[]): MastermindFeedback {
  let black = 0;
  const unmatchedSecret: string[] = [];
  const unmatchedGuess: string[] = [];
  for (let index = 0; index < secret.length; index += 1) {
    if (secret[index] === guess[index]) black += 1;
    else {
      unmatchedSecret.push(secret[index]!);
      unmatchedGuess.push(guess[index]!);
    }
  }
  let white = 0;
  for (const colour of unmatchedGuess) {
    const match = unmatchedSecret.indexOf(colour);
    if (match >= 0) {
      white += 1;
      unmatchedSecret.splice(match, 1);
    }
  }
  return { black, white };
}

export function narrowMastermindCandidates(
  candidates: string[][],
  guess: string[],
  feedback: MastermindFeedback,
): string[][] {
  return candidates.filter((candidate) => {
    const candidateFeedback = scoreMastermindGuess(candidate, guess);
    return candidateFeedback.black === feedback.black && candidateFeedback.white === feedback.white;
  });
}

export async function submitGuess(page: Page): Promise<Response> {
  const responsePromise = page.waitForResponse(
    (response) =>
      /\/v1\/games\/[^/]+\/attempts$/.test(new URL(response.url()).pathname) &&
      response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Submit guess', exact: true }).click();
  return responsePromise;
}

export function desktopOnly(isMobile: boolean | undefined): void {
  expect(isMobile).not.toBe(true);
}
