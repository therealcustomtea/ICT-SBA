// Imports the dependency used by this module.
import { expect, type APIResponse, type Page, type Response } from '@playwright/test';

// Exports this declaration for use by other modules.
export const apiOrigin = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://127.0.0.1:8000';

// Exports this declaration for use by other modules.
export type ProfileResponse = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Defines the displayName field in the surrounding object or type.
  displayName: string | null;
  // Defines the isAnonymous field in the surrounding object or type.
  isAnonymous: boolean;
  // Defines the publicLeaderboards field in the surrounding object or type.
  publicLeaderboards: boolean;
  // Defines the createdAt field in the surrounding object or type.
  createdAt: string;
  // Closes the expression, call, or declaration started above.
};

// Exports this declaration for use by other modules.
export type GameResponse = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Defines the mode field in the surrounding object or type.
  mode: string;
  // Defines the status field in the surrounding object or type.
  status: string;
  // Defines the difficulty field in the surrounding object or type.
  difficulty: string | null;
  // Defines the config field in the surrounding object or type.
  config: {
    // Defines the colours field in the surrounding object or type.
    colours: string[];
    // Defines the codeLength field in the surrounding object or type.
    codeLength: number;
    // Defines the maxAttempts field in the surrounding object or type.
    maxAttempts: number;
    // Defines the duplicatesAllowed field in the surrounding object or type.
    duplicatesAllowed: boolean;
    // Defines the codeMaker field in the surrounding object or type.
    codeMaker: string;
    // Defines the visibility field in the surrounding object or type.
    visibility: string;
    // Defines the ranked field in the surrounding object or type.
    ranked: boolean;
    // Defines the timeBonusCap field in the surrounding object or type.
    timeBonusCap: number;
    // Closes the expression, call, or declaration started above.
  };
  // Defines the attempts field in the surrounding object or type.
  attempts: Array<{
    // Defines the number field in the surrounding object or type.
    number: number;
    // Defines the guess field in the surrounding object or type.
    guess: string[];
    // Defines the feedback field in the surrounding object or type.
    feedback: { black: number; white: number };
    // Closes the expression, call, or declaration started above.
  }>;
  // Defines the attemptsUsed field in the surrounding object or type.
  attemptsUsed: number;
  // Defines the maxAttempts field in the surrounding object or type.
  maxAttempts: number;
  // Defines the attemptsRemaining field in the surrounding object or type.
  attemptsRemaining: number;
  // Executes this line as the next step in the surrounding logic.
  secret?: string[] | null;
  // Defines the ranked field in the surrounding object or type.
  ranked: boolean;
  // Closes the expression, call, or declaration started above.
};

// Exports this declaration for use by other modules.
export type RoomResponse = {
  // Defines the id field in the surrounding object or type.
  id: string;
  // Executes this line as the next step in the surrounding logic.
  roomCode?: string | null;
  // Defines the status field in the surrounding object or type.
  status: string;
  // Defines the config field in the surrounding object or type.
  config: GameResponse['config'];
  // Defines the members field in the surrounding object or type.
  members: Array<{
    // Defines the userId field in the surrounding object or type.
    userId: string;
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
  }>;
  // Defines the winnerId field in the surrounding object or type.
  winnerId: string | null;
  // Defines the isTie field in the surrounding object or type.
  isTie: boolean;
  // Defines the expiresAt field in the surrounding object or type.
  expiresAt: string;
  // Defines the eventSequence field in the surrounding object or type.
  eventSequence: number;
  // Closes the expression, call, or declaration started above.
};

// Exports this declaration for use by other modules.
export type MastermindFeedback = { black: number; white: number };

// Exports this declaration for use by other modules.
export async function captureSession(
  // Defines the page field in the surrounding object or type.
  page: Page,
  // Provides the path value to the surrounding call or element.
  path = '/en/profile',
  // Begins the nested block or object completed below.
): Promise<{ token: string; profile: ProfileResponse }> {
  // Computes and stores profileResponse for subsequent operations.
  const profileResponse = page.waitForResponse(
    // Executes this line as the next step in the surrounding logic.
    (response) =>
      // Calls response.url with the supplied values.
      response.url() === `${apiOrigin}/v1/me/profile` && response.request().method() === 'GET',
    // Closes the expression, call, or declaration started above.
  );
  // Waits for this asynchronous operation to complete.
  await page.goto(path);
  // Computes and stores response for subsequent operations.
  const response = await profileResponse;
  // Computes and stores authorization for subsequent operations.
  const authorization = await response.request().headerValue('authorization');
  // Calls expect with the supplied values.
  expect(authorization).toMatch(/^Bearer \S+$/);
  // Checks this condition before running the nested branch.
  if (!response.ok()) {
    // Computes and stores token for subsequent operations.
    const token = authorization!.slice('Bearer '.length);
    // Executes this line as the next step in the surrounding logic.
    const [encodedHeader = '', encodedClaims = ''] = token.split('.');
    // Computes and stores header for subsequent operations.
    const header = JSON.parse(Buffer.from(encodedHeader, 'base64url').toString('utf8')) as {
      // Executes this line as the next step in the surrounding logic.
      alg?: string;
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores claims for subsequent operations.
    const claims = JSON.parse(Buffer.from(encodedClaims, 'base64url').toString('utf8')) as {
      // Executes this line as the next step in the surrounding logic.
      aud?: string;
      // Executes this line as the next step in the surrounding logic.
      iat?: number;
      // Executes this line as the next step in the surrounding logic.
      iss?: string;
      // Closes the expression, call, or declaration started above.
    };
    // Computes and stores body for subsequent operations.
    const body = (await response.json()) as { code?: string };
    // Throws this error to report an invalid or failed operation.
    throw new Error(
      // Executes this line as the next step in the surrounding logic.
      `Profile bootstrap failed (${response.status()} ${body.code ?? 'UNKNOWN'}; ` +
        // Executes this line as the next step in the surrounding logic.
        `alg=${header.alg ?? 'unknown'}; iss=${claims.iss ?? 'unknown'}; ` +
        // Supplies this item to the surrounding call or collection.
        `aud=${claims.aud ?? 'unknown'}; clockDelta=${(claims.iat ?? 0) - Math.floor(Date.now() / 1000)}s).`,
      // Closes the expression, call, or declaration started above.
    );
    // Closes the expression, call, or declaration started above.
  }
  // Returns this result to the caller and ends the current function.
  return {
    // Defines the token field in the surrounding object or type.
    token: authorization!.slice('Bearer '.length),
    // Defines the profile field in the surrounding object or type.
    profile: (await response.json()) as ProfileResponse,
    // Closes the expression, call, or declaration started above.
  };
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export async function apiRequest(
  // Defines the page field in the surrounding object or type.
  page: Page,
  // Defines the token field in the surrounding object or type.
  token: string,
  // Defines the path field in the surrounding object or type.
  path: string,
  // Defines the options field in the surrounding object or type.
  options: { method?: string; body?: unknown } = {},
  // Begins the nested block or object completed below.
): Promise<APIResponse> {
  // Returns this result to the caller and ends the current function.
  return page.request.fetch(`${apiOrigin}${path}`, {
    // Defines the method field in the surrounding object or type.
    method: options.method ?? 'GET',
    // Defines the headers field in the surrounding object or type.
    headers: {
      // Defines the Authorization field in the surrounding object or type.
      Authorization: `Bearer ${token}`,
      // Supplies this item to the surrounding call or collection.
      ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
      // Closes the expression, call, or declaration started above.
    },
    // Defines the data field in the surrounding object or type.
    data: options.body,
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export async function expectActiveSecretOmitted(
  // Defines the response field in the surrounding object or type.
  response: APIResponse | Response,
  // Supplies this item to the surrounding call or collection.
  knownSecret?: string[],
  // Begins the nested block or object completed below.
): Promise<GameResponse> {
  // Calls expect with the supplied values.
  expect(response.ok()).toBe(true);
  // Computes and stores raw for subsequent operations.
  const raw = await response.text();
  // Computes and stores game for subsequent operations.
  const game = JSON.parse(raw) as GameResponse;
  // Calls expect with the supplied values.
  expect(game.status).toBe('active');
  // Calls expect with the supplied values.
  expect(game.secret ?? null).toBeNull();
  // Checks this condition before running the nested branch.
  if (knownSecret) {
    // Calls expect with the supplied values.
    expect(raw).not.toContain(JSON.stringify(knownSecret));
    // Calls expect with the supplied values.
    expect(raw).not.toContain(knownSecret.join(''));
    // Closes the expression, call, or declaration started above.
  }
  // Returns this result to the caller and ends the current function.
  return game;
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export async function createKnownGame(
  // Defines the page field in the surrounding object or type.
  page: Page,
  // Defines the token field in the surrounding object or type.
  token: string,
  // Begins the nested block or object completed below.
  {
    // Provides the secret value to the surrounding call or element.
    secret = ['R', 'B', 'G', 'Y'],
    // Provides the maxAttempts value to the surrounding call or element.
    maxAttempts = 2,
    // Provides the duplicatesAllowed value to the surrounding call or element.
    duplicatesAllowed = false,
    // Begins the nested block or object completed below.
  }: {
    // Executes this line as the next step in the surrounding logic.
    secret?: string[];
    // Executes this line as the next step in the surrounding logic.
    maxAttempts?: number;
    // Executes this line as the next step in the surrounding logic.
    duplicatesAllowed?: boolean;
    // Supplies this item to the surrounding call or collection.
  } = {},
  // Begins the nested block or object completed below.
): Promise<GameResponse> {
  // Computes and stores colours for subsequent operations.
  const colours = ['R', 'B', 'G', 'Y', 'W'];
  // Computes and stores response for subsequent operations.
  const response = await apiRequest(page, token, '/v1/games', {
    // Defines the method field in the surrounding object or type.
    method: 'POST',
    // Defines the body field in the surrounding object or type.
    body: {
      // Defines the mode field in the surrounding object or type.
      mode: 'pass_and_play',
      // Defines the config field in the surrounding object or type.
      config: {
        // Supplies this item to the surrounding call or collection.
        colours,
        // Defines the codeLength field in the surrounding object or type.
        codeLength: secret.length,
        // Supplies this item to the surrounding call or collection.
        maxAttempts,
        // Supplies this item to the surrounding call or collection.
        duplicatesAllowed,
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
      // Supplies this item to the surrounding call or collection.
      secret,
      // Defines the idempotencyKey field in the surrounding object or type.
      idempotencyKey: crypto.randomUUID(),
      // Closes the expression, call, or declaration started above.
    },
    // Closes the expression, call, or declaration started above.
  });
  // Returns this result to the caller and ends the current function.
  return expectActiveSecretOmitted(response, secret);
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export async function chooseGuess(page: Page, guess: string[]): Promise<void> {
  // Iterates through these values for the nested operation.
  for (const colour of guess) {
    // Waits for this asynchronous operation to complete.
    await page.locator(`.game-workspace .palette .peg-${colour}`).click();
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export async function chooseDuelGuess(page: Page, guess: string[]): Promise<void> {
  // Iterates through these values for the nested operation.
  for (const colour of guess) {
    // Waits for this asynchronous operation to complete.
    await page.locator(`.duel-layout .palette .peg-${colour}`).click();
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function enumerateMastermindCandidates(
  // Defines the colours field in the surrounding object or type.
  colours: string[],
  // Defines the codeLength field in the surrounding object or type.
  codeLength: number,
  // Defines the duplicatesAllowed field in the surrounding object or type.
  duplicatesAllowed: boolean,
  // Begins the nested block or object completed below.
): string[][] {
  // Computes and stores candidates for subsequent operations.
  const candidates: string[][] = [];
  // Computes and stores append for subsequent operations.
  const append = (prefix: string[]) => {
    // Checks this condition before running the nested branch.
    if (prefix.length === codeLength) {
      // Calls candidates.push with the supplied values.
      candidates.push(prefix);
      // Returns this result to the caller and ends the current function.
      return;
      // Closes the expression, call, or declaration started above.
    }
    // Iterates through these values for the nested operation.
    for (const colour of colours) {
      // Checks this condition before running the nested branch.
      if (duplicatesAllowed || !prefix.includes(colour)) append([...prefix, colour]);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  };
  // Calls append with the supplied values.
  append([]);
  // Returns this result to the caller and ends the current function.
  return candidates;
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function scoreMastermindGuess(secret: string[], guess: string[]): MastermindFeedback {
  // Computes and stores black for subsequent operations.
  let black = 0;
  // Computes and stores unmatchedSecret for subsequent operations.
  const unmatchedSecret: string[] = [];
  // Computes and stores unmatchedGuess for subsequent operations.
  const unmatchedGuess: string[] = [];
  // Iterates through these values for the nested operation.
  for (let index = 0; index < secret.length; index += 1) {
    // Checks this condition before running the nested branch.
    if (secret[index] === guess[index]) black += 1;
    // Handles the remaining unmatched case.
    else {
      // Calls unmatchedSecret.push with the supplied values.
      unmatchedSecret.push(secret[index]!);
      // Calls unmatchedGuess.push with the supplied values.
      unmatchedGuess.push(guess[index]!);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  }
  // Computes and stores white for subsequent operations.
  let white = 0;
  // Iterates through these values for the nested operation.
  for (const colour of unmatchedGuess) {
    // Computes and stores match for subsequent operations.
    const match = unmatchedSecret.indexOf(colour);
    // Checks this condition before running the nested branch.
    if (match >= 0) {
      // Executes this line as the next step in the surrounding logic.
      white += 1;
      // Calls unmatchedSecret.splice with the supplied values.
      unmatchedSecret.splice(match, 1);
      // Closes the expression, call, or declaration started above.
    }
    // Closes the expression, call, or declaration started above.
  }
  // Returns this result to the caller and ends the current function.
  return { black, white };
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function narrowMastermindCandidates(
  // Defines the candidates field in the surrounding object or type.
  candidates: string[][],
  // Defines the guess field in the surrounding object or type.
  guess: string[],
  // Defines the feedback field in the surrounding object or type.
  feedback: MastermindFeedback,
  // Begins the nested block or object completed below.
): string[][] {
  // Returns this result to the caller and ends the current function.
  return candidates.filter((candidate) => {
    // Computes and stores candidateFeedback for subsequent operations.
    const candidateFeedback = scoreMastermindGuess(candidate, guess);
    // Returns this result to the caller and ends the current function.
    return candidateFeedback.black === feedback.black && candidateFeedback.white === feedback.white;
    // Closes the expression, call, or declaration started above.
  });
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export async function submitGuess(page: Page): Promise<Response> {
  // Computes and stores responsePromise for subsequent operations.
  const responsePromise = page.waitForResponse(
    // Executes this line as the next step in the surrounding logic.
    (response) =>
      // Executes this line as the next step in the surrounding logic.
      /\/v1\/games\/[^/]+\/attempts$/.test(new URL(response.url()).pathname) &&
      // Calls response.request with the supplied values.
      response.request().method() === 'POST',
    // Closes the expression, call, or declaration started above.
  );
  // Waits for this asynchronous operation to complete.
  await page.getByRole('button', { name: 'Submit guess', exact: true }).click();
  // Returns this result to the caller and ends the current function.
  return responsePromise;
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export function desktopOnly(isMobile: boolean | undefined): void {
  // Calls expect with the supplied values.
  expect(isMobile).not.toBe(true);
  // Closes the expression, call, or declaration started above.
}
