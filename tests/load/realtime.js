// Imports the dependency used by this module.
import http from 'k6/http';
// Imports the dependency used by this module.
import ws from 'k6/ws';
// Imports the dependency used by this module.
import { check, fail } from 'k6';

// Computes and stores apiOrigin for subsequent operations.
const apiOrigin = (__ENV.K6_API_ORIGIN || 'http://127.0.0.1:8000').replace(/\/$/, '');
// Computes and stores wsOrigin for subsequent operations.
const wsOrigin = apiOrigin.replace(/^http/, 'ws');
// Computes and stores targetEnvironment for subsequent operations.
const targetEnvironment = (__ENV.K6_TARGET_ENVIRONMENT || '').trim().toLowerCase();
// Computes and stores singleAccessToken for subsequent operations.
const singleAccessToken = (__ENV.K6_ACCESS_TOKEN || '').trim();
// Computes and stores singleRoomId for subsequent operations.
const singleRoomId = (__ENV.K6_ROOM_ID || '').trim();
// Computes and stores wsVus for subsequent operations.
const wsVus = Number(__ENV.K6_WS_VUS || 1);
// Computes and stores sessionMilliseconds for subsequent operations.
const sessionMilliseconds = Number(__ENV.K6_WS_SESSION_MS || 5000);
// Computes and stores connectionsPerIdentity for subsequent operations.
const connectionsPerIdentity = Number(__ENV.K6_WS_CONNECTIONS_PER_IDENTITY || 3);
// Computes and stores connectionsPerSourceIp for subsequent operations.
const connectionsPerSourceIp = Number(__ENV.K6_WS_CONNECTIONS_PER_SOURCE_IP || 20);
// Computes and stores targetConfigurationError for subsequent operations.
let targetConfigurationError = '';
// Computes and stores targets for subsequent operations.
let targets =
  // Executes this line as the next step in the surrounding logic.
  singleAccessToken && singleRoomId
    // Executes this line as the next step in the surrounding logic.
    ? [{ accessToken: singleAccessToken, roomId: singleRoomId }]
    // Executes this line as the next step in the surrounding logic.
    : [];

// Checks this condition before running the nested branch.
if (__ENV.K6_WS_TARGETS_JSON) {
  // Starts an operation whose expected failures are handled below.
  try {
    // Computes and stores parsed for subsequent operations.
    const parsed = JSON.parse(__ENV.K6_WS_TARGETS_JSON);
    // Checks this condition before running the nested branch.
    if (
      // Executes this line as the next step in the surrounding logic.
      !Array.isArray(parsed) ||
      // Executes this line as the next step in the surrounding logic.
      parsed.length === 0 ||
      // Calls parsed.some with the supplied values.
      parsed.some(
        // Executes this line as the next step in the surrounding logic.
        (target) =>
          // Provides the target value to the surrounding call or element.
          target == null ||
          // Executes this line as the next step in the surrounding logic.
          typeof target.accessToken !== 'string' ||
          // Executes this line as the next step in the surrounding logic.
          !target.accessToken.trim() ||
          // Executes this line as the next step in the surrounding logic.
          typeof target.roomId !== 'string' ||
          // Supplies this item to the surrounding call or collection.
          !target.roomId.trim(),
      // Closes the expression, call, or declaration started above.
      )
    // Begins the nested block or object completed below.
    ) {
      // Provides the targetConfigurationError value to the surrounding call or element.
      targetConfigurationError =
        // Executes this line as the next step in the surrounding logic.
        'K6_WS_TARGETS_JSON must be a non-empty JSON array of accessToken/roomId objects.';
    // Handles the remaining unmatched case.
    } else {
      // Provides the targets value to the surrounding call or element.
      targets = parsed.map((target) => ({
        // Defines the accessToken field in the surrounding object or type.
        accessToken: target.accessToken.trim(),
        // Defines the roomId field in the surrounding object or type.
        roomId: target.roomId.trim(),
      // Closes the expression, call, or declaration started above.
      }));
    // Closes the expression, call, or declaration started above.
    }
  // Handles a failure from the protected operation.
  } catch (_error) {
    // Provides the targetConfigurationError value to the surrounding call or element.
    targetConfigurationError = 'K6_WS_TARGETS_JSON must contain valid JSON.';
  // Closes the expression, call, or declaration started above.
  }
// Closes the expression, call, or declaration started above.
}

// Defines the validateConfiguration function and its callable behavior.
function validateConfiguration() {
  // Checks this condition before running the nested branch.
  if (targetConfigurationError) fail(targetConfigurationError);
  // Checks this condition before running the nested branch.
  if (targets.length === 0) {
    // Calls fail with the supplied values.
    fail(
      // Supplies this item to the surrounding call or collection.
      'K6_ACCESS_TOKEN and K6_ROOM_ID, or K6_WS_TARGETS_JSON, are required for real room members.',
    // Closes the expression, call, or declaration started above.
    );
  // Closes the expression, call, or declaration started above.
  }
  // Checks this condition before running the nested branch.
  if (!Number.isInteger(wsVus) || wsVus < 1) fail('K6_WS_VUS must be a positive integer.');
  // Checks this condition before running the nested branch.
  if (!Number.isInteger(sessionMilliseconds) || sessionMilliseconds < 1000) {
    // Calls fail with the supplied values.
    fail('K6_WS_SESSION_MS must be an integer of at least 1000.');
  // Closes the expression, call, or declaration started above.
  }
  // Checks this condition before running the nested branch.
  if (!Number.isInteger(connectionsPerIdentity) || connectionsPerIdentity < 1) {
    // Calls fail with the supplied values.
    fail('K6_WS_CONNECTIONS_PER_IDENTITY must be a positive integer.');
  // Closes the expression, call, or declaration started above.
  }
  // Checks this condition before running the nested branch.
  if (!Number.isInteger(connectionsPerSourceIp) || connectionsPerSourceIp < 1) {
    // Calls fail with the supplied values.
    fail('K6_WS_CONNECTIONS_PER_SOURCE_IP must be a positive integer.');
  // Closes the expression, call, or declaration started above.
  }
  // Computes and stores distinctIdentityCount for subsequent operations.
  const distinctIdentityCount = new Set(targets.map((target) => target.accessToken)).size;
  // Checks this condition before running the nested branch.
  if (wsVus > distinctIdentityCount * connectionsPerIdentity) {
    // Calls fail with the supplied values.
    fail(
      // Supplies this item to the surrounding call or collection.
      'K6_WS_VUS exceeds the configured per-identity connection budget; add member targets instead of bypassing the deployed limit.',
    // Closes the expression, call, or declaration started above.
    );
  // Closes the expression, call, or declaration started above.
  }
  // Checks this condition before running the nested branch.
  if (wsVus > connectionsPerSourceIp) {
    // Calls fail with the supplied values.
    fail(
      // Supplies this item to the surrounding call or collection.
      'K6_WS_VUS exceeds the configured source-IP connection budget; shard the run across approved generators.',
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
  // Defines the scenarios field in the surrounding object or type.
  scenarios: {
    // Defines the socket_churn field in the surrounding object or type.
    socket_churn: {
      // Defines the executor field in the surrounding object or type.
      executor: 'constant-vus',
      // Defines the vus field in the surrounding object or type.
      vus: wsVus,
      // Defines the duration field in the surrounding object or type.
      duration: __ENV.K6_PROFILE_DURATION || '90s',
    // Closes the expression, call, or declaration started above.
    },
  // Closes the expression, call, or declaration started above.
  },
  // Defines the thresholds field in the surrounding object or type.
  thresholds: {
    // Defines the http_req_failed field in the surrounding object or type.
    http_req_failed: ['rate<0.01'],
    // Supplies this item to the surrounding call or collection.
    'http_req_duration{operation:issue_ws_ticket}': ['p(95)<300'],
    // Defines the checks field in the surrounding object or type.
    checks: ['rate>0.99'],
    // Defines the ws_connecting field in the surrounding object or type.
    ws_connecting: ['p(95)<500'],
    // Defines the ws_session_duration field in the surrounding object or type.
    ws_session_duration: [`p(95)<${sessionMilliseconds + 5000}`],
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

// Defines the targetForVu function and its callable behavior.
function targetForVu() {
  // Returns this result to the caller and ends the current function.
  return targets[(__VU - 1) % targets.length];
// Closes the expression, call, or declaration started above.
}

// Defines the responseHeader function and its callable behavior.
function responseHeader(response, expectedName) {
  // Computes and stores normalizedExpected for subsequent operations.
  const normalizedExpected = expectedName.toLowerCase();
  // Iterates through these values for the nested operation.
  for (const [name, value] of Object.entries(response.headers || {})) {
    // Checks this condition before running the nested branch.
    if (name.toLowerCase() === normalizedExpected) return value;
  // Closes the expression, call, or declaration started above.
  }
  // Returns this result to the caller and ends the current function.
  return '';
// Closes the expression, call, or declaration started above.
}

// Defines the containsCredentialField function and its callable behavior.
function containsCredentialField(value) {
  // Checks this condition before running the nested branch.
  if (Array.isArray(value)) return value.some(containsCredentialField);
  // Checks this condition before running the nested branch.
  if (value == null || typeof value !== 'object') return false;
  // Returns this result to the caller and ends the current function.
  return Object.entries(value).some(([key, child]) => {
    // Computes and stores normalizedKey for subsequent operations.
    const normalizedKey = key.replace(/[_-]/g, '').toLowerCase();
    // Returns this result to the caller and ends the current function.
    return (
      // Calls normalizedKey.includes with the supplied values.
      normalizedKey.includes('secret') ||
      // Calls normalizedKey.includes with the supplied values.
      normalizedKey.includes('ticket') ||
      // Provides the normalizedKey value to the surrounding call or element.
      normalizedKey === 'authorization' ||
      // Provides the normalizedKey value to the surrounding call or element.
      normalizedKey === 'accesstoken' ||
      // Calls containsCredentialField with the supplied values.
      containsCredentialField(child)
    // Closes the expression, call, or declaration started above.
    );
  // Closes the expression, call, or declaration started above.
  });
// Closes the expression, call, or declaration started above.
}

// Exports this declaration as the module default.
export default function () {
  // Executes this line as the next step in the surrounding logic.
  const { accessToken, roomId } = targetForVu();
  // Computes and stores ticketResponse for subsequent operations.
  const ticketResponse = http.post(
    // Supplies this item to the surrounding call or collection.
    `${apiOrigin}/v1/rooms/${encodeURIComponent(roomId)}/ws-ticket`,
    // Supplies this item to the surrounding call or collection.
    null,
    // Begins the nested block or object completed below.
    {
      // Defines the headers field in the surrounding object or type.
      headers: { Authorization: `Bearer ${accessToken}` },
      // Defines the tags field in the surrounding object or type.
      tags: { operation: 'issue_ws_ticket' },
    // Closes the expression, call, or declaration started above.
    },
  // Closes the expression, call, or declaration started above.
  );
  // Checks this condition before running the nested branch.
  if (!check(ticketResponse, { 'ticket issued': (response) => response.status === 200 })) return;

  // Computes and stores ticketPayload for subsequent operations.
  let ticketPayload;
  // Starts an operation whose expected failures are handled below.
  try {
    // Provides the ticketPayload value to the surrounding call or element.
    ticketPayload = ticketResponse.json();
  // Handles a failure from the protected operation.
  } catch (_error) {
    // Calls check with the supplied values.
    check(false, { 'ticket response is valid JSON': (value) => value });
    // Returns this result to the caller and ends the current function.
    return;
  // Closes the expression, call, or declaration started above.
  }
  // Checks this condition before running the nested branch.
  if (ticketPayload == null || typeof ticketPayload !== 'object') {
    // Calls check with the supplied values.
    check(false, { 'ticket response is an object': (value) => value });
    // Returns this result to the caller and ends the current function.
    return;
  // Closes the expression, call, or declaration started above.
  }
  // Computes and stores ticket for subsequent operations.
  const ticket = ticketPayload.ticket;
  // Computes and stores ticketIsValid for subsequent operations.
  const ticketIsValid = check(ticketPayload, {
    // Executes this line as the next step in the surrounding logic.
    'ticket is bounded base64url': (value) =>
      // Executes this line as the next step in the surrounding logic.
      typeof value.ticket === 'string' &&
      // Executes this line as the next step in the surrounding logic.
      value.ticket.length > 0 &&
      // Executes this line as the next step in the surrounding logic.
      value.ticket.length <= 128 &&
      // Supplies this item to the surrounding call or collection.
      /^[A-Za-z0-9_-]+$/.test(value.ticket),
    // Begins the nested block or object completed below.
    'ticket has a short future expiry': (value) => {
      // Computes and stores millisecondsRemaining for subsequent operations.
      const millisecondsRemaining = Date.parse(value.expiresAt) - Date.now();
      // Returns this result to the caller and ends the current function.
      return (
        // Calls Number.isFinite with the supplied values.
        Number.isFinite(millisecondsRemaining) &&
        // Executes this line as the next step in the surrounding logic.
        millisecondsRemaining > 0 &&
        // Executes this line as the next step in the surrounding logic.
        millisecondsRemaining <= 65000
      // Closes the expression, call, or declaration started above.
      );
    // Closes the expression, call, or declaration started above.
    },
  // Closes the expression, call, or declaration started above.
  });
  // Checks this condition before running the nested branch.
  if (!ticketIsValid) return;

  // Computes and stores heartbeatAcknowledged for subsequent operations.
  let heartbeatAcknowledged = false;
  // Computes and stores response for subsequent operations.
  const response = ws.connect(
    // Supplies this item to the surrounding call or collection.
    `${wsOrigin}/v1/rooms/${encodeURIComponent(roomId)}/events?after=0`,
    // Begins the nested block or object completed below.
    {
      // Defines the headers field in the surrounding object or type.
      headers: {
        // Supplies this item to the surrounding call or collection.
        'Sec-WebSocket-Protocol': `cipherboard-v1, ticket.${ticket}`,
      // Closes the expression, call, or declaration started above.
      },
      // Defines the tags field in the surrounding object or type.
      tags: { operation: 'room_events' },
    // Closes the expression, call, or declaration started above.
    },
    // Begins the nested block or object completed below.
    (socket) => {
      // Calls socket.on with the supplied values.
      socket.on('open', () => {
        // Calls socket.send with the supplied values.
        socket.send(JSON.stringify({ version: 1, type: 'heartbeat' }));
        // Calls socket.setTimeout with the supplied values.
        socket.setTimeout(() => socket.close(), sessionMilliseconds);
      // Closes the expression, call, or declaration started above.
      });
      // Calls socket.on with the supplied values.
      socket.on('message', (message) => {
        // Computes and stores event for subsequent operations.
        let event;
        // Starts an operation whose expected failures are handled below.
        try {
          // Provides the event value to the surrounding call or element.
          event = JSON.parse(message);
        // Handles a failure from the protected operation.
        } catch (_error) {
          // Calls check with the supplied values.
          check(false, { 'server event is valid JSON': (value) => value });
          // Returns this result to the caller and ends the current function.
          return;
        // Closes the expression, call, or declaration started above.
        }
        // Checks this condition before running the nested branch.
        if (event.type === 'heartbeat_ack') heartbeatAcknowledged = true;
        // Calls check with the supplied values.
        check(event, {
          // Supplies this item to the surrounding call or collection.
          'event uses protocol version 1': (value) => value.version === 1,
          // Executes this line as the next step in the surrounding logic.
          'event has a type and payload': (value) =>
            // Executes this line as the next step in the surrounding logic.
            typeof value.type === 'string' &&
            // Executes this line as the next step in the surrounding logic.
            value.payload != null &&
            // Supplies this item to the surrounding call or collection.
            typeof value.payload === 'object',
          // Executes this line as the next step in the surrounding logic.
          'event sequence is integer or null': (value) =>
            // Calls Number.isInteger with the supplied values.
            Number.isInteger(value.sequence) || value.sequence == null,
          // Executes this line as the next step in the surrounding logic.
          'event does not expose credentials or secret material': (value) =>
            // Supplies this item to the surrounding call or collection.
            !containsCredentialField(value),
        // Closes the expression, call, or declaration started above.
        });
      // Closes the expression, call, or declaration started above.
      });
      // Calls socket.on with the supplied values.
      socket.on('close', () => {
        // Calls check with the supplied values.
        check(heartbeatAcknowledged, {
          // Supplies this item to the surrounding call or collection.
          'heartbeat acknowledged before close': (value) => value === true,
        // Closes the expression, call, or declaration started above.
        });
      // Closes the expression, call, or declaration started above.
      });
    // Closes the expression, call, or declaration started above.
    },
  // Closes the expression, call, or declaration started above.
  );

  // Calls check with the supplied values.
  check(response, {
    // Supplies this item to the surrounding call or collection.
    'websocket upgraded': (value) => value && value.status === 101,
    // Executes this line as the next step in the surrounding logic.
    'server negotiated only cipherboard-v1': (value) =>
      // Supplies this item to the surrounding call or collection.
      value && responseHeader(value, 'Sec-WebSocket-Protocol') === 'cipherboard-v1',
  // Closes the expression, call, or declaration started above.
  });
// Closes the expression, call, or declaration started above.
}
