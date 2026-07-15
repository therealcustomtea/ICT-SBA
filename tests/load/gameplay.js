import http from 'k6/http';
import { check, fail } from 'k6';

const apiOrigin = (__ENV.K6_API_ORIGIN || 'http://127.0.0.1:8000').replace(/\/$/, '');
const targetEnvironment = (__ENV.K6_TARGET_ENVIRONMENT || '').trim().toLowerCase();
const accessToken = (__ENV.K6_ACCESS_TOKEN || '').trim();
let tokenConfigurationError = '';
let accessTokens = accessToken ? [accessToken] : [];

if (__ENV.K6_ACCESS_TOKENS_JSON) {
  try {
    const parsed = JSON.parse(__ENV.K6_ACCESS_TOKENS_JSON);
    if (
      !Array.isArray(parsed) ||
      parsed.some((token) => typeof token !== 'string' || !token.trim())
    ) {
      tokenConfigurationError = 'K6_ACCESS_TOKENS_JSON must be a JSON array of non-empty tokens.';
    } else {
      accessTokens = parsed.map((token) => token.trim());
    }
  } catch (_error) {
    tokenConfigurationError = 'K6_ACCESS_TOKENS_JSON must contain valid JSON.';
  }
}

function validateConfiguration() {
  if (tokenConfigurationError) fail(tokenConfigurationError);
  if (accessTokens.length === 0) {
    fail(
      'K6_ACCESS_TOKEN or K6_ACCESS_TOKENS_JSON is required; load tests use real authenticated test identities.',
    );
  }
  if (!/^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$/i.test(apiOrigin)) {
    if (!targetEnvironment) {
      fail('K6_TARGET_ENVIRONMENT is required for every non-loopback load target.');
    }
    if (targetEnvironment === 'production' && __ENV.K6_ALLOW_PRODUCTION !== 'true') {
      fail('Refusing to target production without K6_ALLOW_PRODUCTION=true.');
    }
  }
}

export const options = {
  discardResponseBodies: false,
  scenarios: {
    gameplay: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.K6_GAME_RATE || 1),
      timeUnit: __ENV.K6_GAME_TIME_UNIT || '5s',
      duration: __ENV.K6_PROFILE_DURATION || '2m',
      preAllocatedVUs: Number(__ENV.K6_PREALLOCATED_VUS || 2),
      maxVUs: Number(__ENV.K6_MAX_VUS || 10),
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{operation:create_game}': ['p(95)<300'],
    'http_req_duration{operation:submit_attempt}': ['p(95)<250'],
    'http_req_duration{operation:leaderboard}': ['p(95)<300'],
    checks: ['rate>0.99'],
  },
};

export function setup() {
  validateConfiguration();
}

function tokenForIteration() {
  return accessTokens[(__VU + __ITER - 2) % accessTokens.length];
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
    'X-Request-ID': `k6-${randomString(24)}`,
  };
}

function randomString(length) {
  const alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let value = `${__VU}-${__ITER}-`;
  while (value.length < length) {
    value += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return value.slice(0, length);
}

export default function () {
  const token = tokenForIteration();
  const creationKey = `k6-create-${randomString(24)}`;
  const create = http.post(
    `${apiOrigin}/v1/games`,
    JSON.stringify({
      mode: 'solo',
      difficulty: 'easy',
      idempotencyKey: creationKey,
    }),
    { headers: headers(token), tags: { operation: 'create_game' } },
  );

  const created = check(create, {
    'game created': (response) => response.status === 201,
    'active creation does not expose secret': (response) => {
      if (response.status !== 201) return false;
      const body = response.json();
      return body.status !== 'active' || body.secret == null;
    },
  });
  if (!created) return;

  const gameId = create.json('id');
  const attempt = http.post(
    `${apiOrigin}/v1/games/${encodeURIComponent(gameId)}/attempts`,
    JSON.stringify({
      guess: ['R', 'B', 'G', 'Y'],
      idempotencyKey: `k6-attempt-${randomString(24)}`,
    }),
    { headers: headers(token), tags: { operation: 'submit_attempt' } },
  );

  check(attempt, {
    'attempt accepted': (response) => response.status === 200,
    'active attempt does not expose secret': (response) => {
      if (response.status !== 200) return false;
      const body = response.json();
      return body.status !== 'active' || body.secret == null;
    },
  });

  const leaderboard = http.get(`${apiOrigin}/v1/leaderboards?page=1&page_size=25`, {
    headers: headers(token),
    tags: { operation: 'leaderboard' },
  });
  check(leaderboard, {
    'leaderboard bounded read succeeds': (response) => response.status === 200,
  });
}
