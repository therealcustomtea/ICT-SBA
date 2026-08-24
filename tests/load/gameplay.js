// Imports the dependency used by this module.
import http from 'k6/http';
// Imports the dependency used by this module.
import { check, fail } from 'k6';

// Computes and stores apiOrigin for subsequent operations.
const apiOrigin = (__ENV.K6_API_ORIGIN || 'http://127.0.0.1:8000').replace(/\/$/, '');
// Computes and stores targetEnvironment for subsequent operations.
const targetEnvironment = (__ENV.K6_TARGET_ENVIRONMENT || '').trim().toLowerCase();
// Computes and stores accessToken for subsequent operations.
const accessToken = (__ENV.K6_ACCESS_TOKEN || '').trim();
// Computes and stores tokenConfigurationError for subsequent operations.
let tokenConfigurationError = '';
// Computes and stores accessTokens for subsequent operations.
let accessTokens = accessToken ? [accessToken] : [];

// Checks this condition before running the nested branch.
if (__ENV.K6_ACCESS_TOKENS_JSON) {
  // Starts an operation whose expected failures are handled below.
  try {
    // Computes and stores parsed for subsequent operations.
    const parsed = JSON.parse(__ENV.K6_ACCESS_TOKENS_JSON);
    // Checks this condition before running the nested branch.
    if (
      // Executes this line as the next step in the surrounding logic.
      !Array.isArray(parsed) ||
      // Calls parsed.some with the supplied values.
      parsed.some((token) => typeof token !== 'string' || !token.trim())
    // Begins the nested block or object completed below.
    ) {
      // Provides the tokenConfigurationError value to the surrounding call or element.
      tokenConfigurationError = 'K6_ACCESS_TOKENS_JSON must be a JSON array of non-empty tokens.';
    // Handles the remaining unmatched case.
    } else {
      // Provides the accessTokens value to the surrounding call or element.
      accessTokens = parsed.map((token) => token.trim());
    // Closes the expression, call, or declaration started above.
    }
  // Handles a failure from the protected operation.
  } catch (_error) {
    // Provides the tokenConfigurationError value to the surrounding call or element.
    tokenConfigurationError = 'K6_ACCESS_TOKENS_JSON must contain valid JSON.';
  // Closes the expression, call, or declaration started above.
  }
// Closes the expression, call, or declaration started above.
}

// Defines the validateConfiguration function and its callable behavior.
function validateConfiguration() {
  // Checks this condition before running the nested branch.
  if (tokenConfigurationError) fail(tokenConfigurationError);
  // Checks this condition before running the nested branch.
  if (accessTokens.length === 0) {
    // Calls fail with the supplied values.
    fail(
      // Supplies this item to the surrounding call or collection.
      'K6_ACCESS_TOKEN or K6_ACCESS_TOKENS_JSON is required; load tests use real authenticated test identities.',
    // Closes the expression, call, or declaration started above.
    );
  // Closes the expression, call, or declaration started above.
  }
  // Checks this condition before running the nested branch.
  if (!/^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$/i.test(apiOrigin)) {
    // Checks this condition before running the nested branch.
    if (!targetEnvironment) {
      // Calls fail with the supplied values.
      fail('K6_TARGET_ENVIRONMENT is required for every non-loopback load target.');
    // Closes the expression, call, or declaration started above.
    }
    // Checks this condition before running the nested branch.
    if (targetEnvironment === 'production' && __ENV.K6_ALLOW_PRODUCTION !== 'true') {
      // Calls fail with the supplied values.
      fail('Refusing to target production without K6_ALLOW_PRODUCTION=true.');
    // Closes the expression, call, or declaration started above.
    }
  // Closes the expression, call, or declaration started above.
  }
// Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export const options = {
  // Defines the discardResponseBodies field in the surrounding object or type.
  discardResponseBodies: false,
  // Defines the scenarios field in the surrounding object or type.
  scenarios: {
    // Defines the gameplay field in the surrounding object or type.
    gameplay: {
      // Defines the executor field in the surrounding object or type.
      executor: 'constant-arrival-rate',
      // Defines the rate field in the surrounding object or type.
      rate: Number(__ENV.K6_GAME_RATE || 1),
      // Defines the timeUnit field in the surrounding object or type.
      timeUnit: __ENV.K6_GAME_TIME_UNIT || '5s',
      // Defines the duration field in the surrounding object or type.
      duration: __ENV.K6_PROFILE_DURATION || '2m',
      // Defines the preAllocatedVUs field in the surrounding object or type.
      preAllocatedVUs: Number(__ENV.K6_PREALLOCATED_VUS || 2),
      // Defines the maxVUs field in the surrounding object or type.
      maxVUs: Number(__ENV.K6_MAX_VUS || 10),
    // Closes the expression, call, or declaration started above.
    },
  // Closes the expression, call, or declaration started above.
  },
  // Defines the thresholds field in the surrounding object or type.
  thresholds: {
    // Defines the http_req_failed field in the surrounding object or type.
    http_req_failed: ['rate<0.01'],
    // Supplies this item to the surrounding call or collection.
    'http_req_duration{operation:create_game}': ['p(95)<300'],
    // Supplies this item to the surrounding call or collection.
    'http_req_duration{operation:submit_attempt}': ['p(95)<250'],
    // Supplies this item to the surrounding call or collection.
    'http_req_duration{operation:leaderboard}': ['p(95)<300'],
    // Defines the checks field in the surrounding object or type.
    checks: ['rate>0.99'],
  // Closes the expression, call, or declaration started above.
  },
// Closes the expression, call, or declaration started above.
};

// Exports this declaration for use by other modules.
export function setup() {
  // Calls validateConfiguration with the supplied values.
  validateConfiguration();
// Closes the expression, call, or declaration started above.
}

// Defines the tokenForIteration function and its callable behavior.
function tokenForIteration() {
  // Returns this result to the caller and ends the current function.
  return accessTokens[(__VU + __ITER - 2) % accessTokens.length];
// Closes the expression, call, or declaration started above.
}

// Defines the headers function and its callable behavior.
function headers(token) {
  // Returns this result to the caller and ends the current function.
  return {
    // Defines the Authorization field in the surrounding object or type.
    Authorization: `Bearer ${token}`,
    // Supplies this item to the surrounding call or collection.
    'Content-Type': 'application/json',
    // Supplies this item to the surrounding call or collection.
    'X-Request-ID': `k6-${randomString(24)}`,
  // Closes the expression, call, or declaration started above.
  };
// Closes the expression, call, or declaration started above.
}

// Defines the randomString function and its callable behavior.
function randomString(length) {
  // Computes and stores alphabet for subsequent operations.
  const alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  // Computes and stores value for subsequent operations.
  let value = `${__VU}-${__ITER}-`;
  // Repeats this block while the condition remains true.
  while (value.length < length) {
    // Executes this line as the next step in the surrounding logic.
    value += alphabet[Math.floor(Math.random() * alphabet.length)];
  // Closes the expression, call, or declaration started above.
  }
  // Returns this result to the caller and ends the current function.
  return value.slice(0, length);
// Closes the expression, call, or declaration started above.
}

// Exports this declaration as the module default.
export default function () {
  // Computes and stores token for subsequent operations.
  const token = tokenForIteration();
  // Computes and stores creationKey for subsequent operations.
  const creationKey = `k6-create-${randomString(24)}`;
  // Computes and stores create for subsequent operations.
  const create = http.post(
    // Supplies this item to the surrounding call or collection.
    `${apiOrigin}/v1/games`,
    // Calls JSON.stringify with the supplied values.
    JSON.stringify({
      // Defines the mode field in the surrounding object or type.
      mode: 'solo',
      // Defines the difficulty field in the surrounding object or type.
      difficulty: 'easy',
      // Defines the idempotencyKey field in the surrounding object or type.
      idempotencyKey: creationKey,
    // Closes the expression, call, or declaration started above.
    }),
    // Supplies this item to the surrounding call or collection.
    { headers: headers(token), tags: { operation: 'create_game' } },
  // Closes the expression, call, or declaration started above.
  );

  // Computes and stores created for subsequent operations.
  const created = check(create, {
    // Supplies this item to the surrounding call or collection.
    'game created': (response) => response.status === 201,
    // Begins the nested block or object completed below.
    'active creation does not expose secret': (response) => {
      // Checks this condition before running the nested branch.
      if (response.status !== 201) return false;
      // Computes and stores body for subsequent operations.
      const body = response.json();
      // Returns this result to the caller and ends the current function.
      return body.status !== 'active' || body.secret == null;
    // Closes the expression, call, or declaration started above.
    },
  // Closes the expression, call, or declaration started above.
  });
  // Checks this condition before running the nested branch.
  if (!created) return;

  // Computes and stores gameId for subsequent operations.
  const gameId = create.json('id');
  // Computes and stores attempt for subsequent operations.
  const attempt = http.post(
    // Supplies this item to the surrounding call or collection.
    `${apiOrigin}/v1/games/${encodeURIComponent(gameId)}/attempts`,
    // Calls JSON.stringify with the supplied values.
    JSON.stringify({
      // Defines the guess field in the surrounding object or type.
      guess: ['R', 'B', 'G', 'Y'],
      // Defines the idempotencyKey field in the surrounding object or type.
      idempotencyKey: `k6-attempt-${randomString(24)}`,
    // Closes the expression, call, or declaration started above.
    }),
    // Supplies this item to the surrounding call or collection.
    { headers: headers(token), tags: { operation: 'submit_attempt' } },
  // Closes the expression, call, or declaration started above.
  );

  // Calls check with the supplied values.
  check(attempt, {
    // Supplies this item to the surrounding call or collection.
    'attempt accepted': (response) => response.status === 200,
    // Begins the nested block or object completed below.
    'active attempt does not expose secret': (response) => {
      // Checks this condition before running the nested branch.
      if (response.status !== 200) return false;
      // Computes and stores body for subsequent operations.
      const body = response.json();
      // Returns this result to the caller and ends the current function.
      return body.status !== 'active' || body.secret == null;
    // Closes the expression, call, or declaration started above.
    },
  // Closes the expression, call, or declaration started above.
  });

  // Computes and stores leaderboard for subsequent operations.
  const leaderboard = http.get(`${apiOrigin}/v1/leaderboards?page=1&page_size=25`, {
    // Defines the headers field in the surrounding object or type.
    headers: headers(token),
    // Defines the tags field in the surrounding object or type.
    tags: { operation: 'leaderboard' },
  // Closes the expression, call, or declaration started above.
  });
  // Calls check with the supplied values.
  check(leaderboard, {
    // Supplies this item to the surrounding call or collection.
    'leaderboard bounded read succeeds': (response) => response.status === 200,
  // Closes the expression, call, or declaration started above.
  });
// Closes the expression, call, or declaration started above.
}
