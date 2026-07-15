import http from 'k6/http';
import ws from 'k6/ws';
import { check, fail } from 'k6';

const apiOrigin = (__ENV.K6_API_ORIGIN || 'http://127.0.0.1:8000').replace(/\/$/, '');
const wsOrigin = apiOrigin.replace(/^http/, 'ws');
const targetEnvironment = (__ENV.K6_TARGET_ENVIRONMENT || '').trim().toLowerCase();
const singleAccessToken = (__ENV.K6_ACCESS_TOKEN || '').trim();
const singleRoomId = (__ENV.K6_ROOM_ID || '').trim();
const wsVus = Number(__ENV.K6_WS_VUS || 1);
const sessionMilliseconds = Number(__ENV.K6_WS_SESSION_MS || 5000);
const connectionsPerIdentity = Number(__ENV.K6_WS_CONNECTIONS_PER_IDENTITY || 3);
const connectionsPerSourceIp = Number(__ENV.K6_WS_CONNECTIONS_PER_SOURCE_IP || 20);
let targetConfigurationError = '';
let targets =
  singleAccessToken && singleRoomId
    ? [{ accessToken: singleAccessToken, roomId: singleRoomId }]
    : [];

if (__ENV.K6_WS_TARGETS_JSON) {
  try {
    const parsed = JSON.parse(__ENV.K6_WS_TARGETS_JSON);
    if (
      !Array.isArray(parsed) ||
      parsed.length === 0 ||
      parsed.some(
        (target) =>
          target == null ||
          typeof target.accessToken !== 'string' ||
          !target.accessToken.trim() ||
          typeof target.roomId !== 'string' ||
          !target.roomId.trim(),
      )
    ) {
      targetConfigurationError =
        'K6_WS_TARGETS_JSON must be a non-empty JSON array of accessToken/roomId objects.';
    } else {
      targets = parsed.map((target) => ({
        accessToken: target.accessToken.trim(),
        roomId: target.roomId.trim(),
      }));
    }
  } catch (_error) {
    targetConfigurationError = 'K6_WS_TARGETS_JSON must contain valid JSON.';
  }
}

function validateConfiguration() {
  if (targetConfigurationError) fail(targetConfigurationError);
  if (targets.length === 0) {
    fail(
      'K6_ACCESS_TOKEN and K6_ROOM_ID, or K6_WS_TARGETS_JSON, are required for real room members.',
    );
  }
  if (!Number.isInteger(wsVus) || wsVus < 1) fail('K6_WS_VUS must be a positive integer.');
  if (!Number.isInteger(sessionMilliseconds) || sessionMilliseconds < 1000) {
    fail('K6_WS_SESSION_MS must be an integer of at least 1000.');
  }
  if (!Number.isInteger(connectionsPerIdentity) || connectionsPerIdentity < 1) {
    fail('K6_WS_CONNECTIONS_PER_IDENTITY must be a positive integer.');
  }
  if (!Number.isInteger(connectionsPerSourceIp) || connectionsPerSourceIp < 1) {
    fail('K6_WS_CONNECTIONS_PER_SOURCE_IP must be a positive integer.');
  }
  const distinctIdentityCount = new Set(targets.map((target) => target.accessToken)).size;
  if (wsVus > distinctIdentityCount * connectionsPerIdentity) {
    fail(
      'K6_WS_VUS exceeds the configured per-identity connection budget; add member targets instead of bypassing the deployed limit.',
    );
  }
  if (wsVus > connectionsPerSourceIp) {
    fail(
      'K6_WS_VUS exceeds the configured source-IP connection budget; shard the run across approved generators.',
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
  scenarios: {
    socket_churn: {
      executor: 'constant-vus',
      vus: wsVus,
      duration: __ENV.K6_PROFILE_DURATION || '90s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{operation:issue_ws_ticket}': ['p(95)<300'],
    checks: ['rate>0.99'],
    ws_connecting: ['p(95)<500'],
    ws_session_duration: [`p(95)<${sessionMilliseconds + 5000}`],
  },
};

export function setup() {
  validateConfiguration();
}

function targetForVu() {
  return targets[(__VU - 1) % targets.length];
}

function responseHeader(response, expectedName) {
  const normalizedExpected = expectedName.toLowerCase();
  for (const [name, value] of Object.entries(response.headers || {})) {
    if (name.toLowerCase() === normalizedExpected) return value;
  }
  return '';
}

function containsCredentialField(value) {
  if (Array.isArray(value)) return value.some(containsCredentialField);
  if (value == null || typeof value !== 'object') return false;
  return Object.entries(value).some(([key, child]) => {
    const normalizedKey = key.replace(/[_-]/g, '').toLowerCase();
    return (
      normalizedKey.includes('secret') ||
      normalizedKey.includes('ticket') ||
      normalizedKey === 'authorization' ||
      normalizedKey === 'accesstoken' ||
      containsCredentialField(child)
    );
  });
}

export default function () {
  const { accessToken, roomId } = targetForVu();
  const ticketResponse = http.post(
    `${apiOrigin}/v1/rooms/${encodeURIComponent(roomId)}/ws-ticket`,
    null,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
      tags: { operation: 'issue_ws_ticket' },
    },
  );
  if (!check(ticketResponse, { 'ticket issued': (response) => response.status === 200 })) return;

  let ticketPayload;
  try {
    ticketPayload = ticketResponse.json();
  } catch (_error) {
    check(false, { 'ticket response is valid JSON': (value) => value });
    return;
  }
  if (ticketPayload == null || typeof ticketPayload !== 'object') {
    check(false, { 'ticket response is an object': (value) => value });
    return;
  }
  const ticket = ticketPayload.ticket;
  const ticketIsValid = check(ticketPayload, {
    'ticket is bounded base64url': (value) =>
      typeof value.ticket === 'string' &&
      value.ticket.length > 0 &&
      value.ticket.length <= 128 &&
      /^[A-Za-z0-9_-]+$/.test(value.ticket),
    'ticket has a short future expiry': (value) => {
      const millisecondsRemaining = Date.parse(value.expiresAt) - Date.now();
      return (
        Number.isFinite(millisecondsRemaining) &&
        millisecondsRemaining > 0 &&
        millisecondsRemaining <= 65000
      );
    },
  });
  if (!ticketIsValid) return;

  let heartbeatAcknowledged = false;
  const response = ws.connect(
    `${wsOrigin}/v1/rooms/${encodeURIComponent(roomId)}/events?after=0`,
    {
      headers: {
        'Sec-WebSocket-Protocol': `cipherboard-v1, ticket.${ticket}`,
      },
      tags: { operation: 'room_events' },
    },
    (socket) => {
      socket.on('open', () => {
        socket.send(JSON.stringify({ version: 1, type: 'heartbeat' }));
        socket.setTimeout(() => socket.close(), sessionMilliseconds);
      });
      socket.on('message', (message) => {
        let event;
        try {
          event = JSON.parse(message);
        } catch (_error) {
          check(false, { 'server event is valid JSON': (value) => value });
          return;
        }
        if (event.type === 'heartbeat_ack') heartbeatAcknowledged = true;
        check(event, {
          'event uses protocol version 1': (value) => value.version === 1,
          'event has a type and payload': (value) =>
            typeof value.type === 'string' &&
            value.payload != null &&
            typeof value.payload === 'object',
          'event sequence is integer or null': (value) =>
            Number.isInteger(value.sequence) || value.sequence == null,
          'event does not expose credentials or secret material': (value) =>
            !containsCredentialField(value),
        });
      });
      socket.on('close', () => {
        check(heartbeatAcknowledged, {
          'heartbeat acknowledged before close': (value) => value === true,
        });
      });
    },
  );

  check(response, {
    'websocket upgraded': (value) => value && value.status === 101,
    'server negotiated only cipherboard-v1': (value) =>
      value && responseHeader(value, 'Sec-WebSocket-Protocol') === 'cipherboard-v1',
  });
}
