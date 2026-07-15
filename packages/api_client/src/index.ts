import type { components, paths } from './schema.js';

export type ApiPaths = paths;
export type ApiComponents = components;

export type ApiErrorBody = {
  code: string;
  message: string;
  requestId: string;
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: ApiErrorBody,
  ) {
    super(body.message);
    this.name = 'ApiError';
  }
}

export class MastermindApi {
  constructor(
    private readonly baseUrl: string,
    private readonly getToken: () => Promise<string | null>,
  ) {}

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const token = await this.getToken();
    const headers = new Headers(init.headers);
    headers.set('Accept', 'application/json');
    if (init.body) headers.set('Content-Type', 'application/json');
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const response = await fetch(`${this.baseUrl}${path}`, { ...init, cache: 'no-store', headers });
    if (!response.ok) {
      let body: ApiErrorBody;
      try {
        body = (await response.json()) as ApiErrorBody;
      } catch {
        body = {
          code: 'UNEXPECTED_ERROR',
          message: 'The request could not be completed.',
          requestId: response.headers.get('x-request-id') ?? '',
        };
      }
      throw new ApiError(response.status, body);
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }
}
