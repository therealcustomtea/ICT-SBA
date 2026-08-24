// Imports the dependency used by this module.
import type { components, paths } from './schema.js';

// Exports this declaration for use by other modules.
export type ApiPaths = paths;
// Exports this declaration for use by other modules.
export type ApiComponents = components;

// Exports this declaration for use by other modules.
export type ApiErrorBody = {
  // Defines the code field in the surrounding object or type.
  code: string;
  // Defines the message field in the surrounding object or type.
  message: string;
  // Defines the requestId field in the surrounding object or type.
  requestId: string;
  // Closes the expression, call, or declaration started above.
};

// Exports this declaration for use by other modules.
export class ApiError extends Error {
  // Calls constructor with the supplied values.
  constructor(
    // Supplies this item to the surrounding call or collection.
    public readonly status: number,
    // Supplies this item to the surrounding call or collection.
    public readonly body: ApiErrorBody,
    // Begins the nested block or object completed below.
  ) {
    // Calls super with the supplied values.
    super(body.message);
    // Executes this line as the next step in the surrounding logic.
    this.name = 'ApiError';
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}

// Exports this declaration for use by other modules.
export class MastermindApi {
  // Calls constructor with the supplied values.
  constructor(
    // Supplies this item to the surrounding call or collection.
    private readonly baseUrl: string,
    // Supplies this item to the surrounding call or collection.
    private readonly getToken: () => Promise<string | null>,
    // Executes this line as the next step in the surrounding logic.
  ) {}

  // Begins the nested block or object completed below.
  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    // Computes and stores token for subsequent operations.
    const token = await this.getToken();
    // Computes and stores headers for subsequent operations.
    const headers = new Headers(init.headers);
    // Calls headers.set with the supplied values.
    headers.set('Accept', 'application/json');
    // Checks this condition before running the nested branch.
    if (init.body) headers.set('Content-Type', 'application/json');
    // Checks this condition before running the nested branch.
    if (token) headers.set('Authorization', `Bearer ${token}`);
    // Computes and stores response for subsequent operations.
    const response = await fetch(`${this.baseUrl}${path}`, { ...init, cache: 'no-store', headers });
    // Checks this condition before running the nested branch.
    if (!response.ok) {
      // Computes and stores body for subsequent operations.
      let body: ApiErrorBody;
      // Starts an operation whose expected failures are handled below.
      try {
        // Provides the body value to the surrounding call or element.
        body = (await response.json()) as ApiErrorBody;
        // Handles a failure from the protected operation.
      } catch {
        // Provides the body value to the surrounding call or element.
        body = {
          // Defines the code field in the surrounding object or type.
          code: 'UNEXPECTED_ERROR',
          // Defines the message field in the surrounding object or type.
          message: 'The request could not be completed.',
          // Defines the requestId field in the surrounding object or type.
          requestId: response.headers.get('x-request-id') ?? '',
          // Closes the expression, call, or declaration started above.
        };
        // Closes the expression, call, or declaration started above.
      }
      // Throws this error to report an invalid or failed operation.
      throw new ApiError(response.status, body);
      // Closes the expression, call, or declaration started above.
    }
    // Checks this condition before running the nested branch.
    if (response.status === 204) return undefined as T;
    // Returns this result to the caller and ends the current function.
    return (await response.json()) as T;
    // Closes the expression, call, or declaration started above.
  }
  // Closes the expression, call, or declaration started above.
}
