/** Typed API client.
 *
 * In development the Next.js rewrite proxies `/api/*` to the backend, so we use
 * relative URLs. When the backend is unreachable, callers fall back to mock
 * data (see `src/lib/mock.ts`) so the UI is always demonstrable.
 */

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
  }
}

function authHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = window.localStorage.getItem("tmai_access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
      ...(options.headers ?? {}),
    },
  });

  if (!res.ok) {
    let code = "ERROR";
    let message = res.statusText;
    try {
      const body = await res.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
    } catch {
      /* ignore parse failures */
    }
    throw new ApiError(res.status, code, message);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Run an API call, falling back to mock data when the backend is unavailable. */
export async function withFallback<T>(
  call: () => Promise<T>,
  fallback: () => T
): Promise<{ data: T; live: boolean }> {
  try {
    const data = await call();
    return { data, live: true };
  } catch {
    return { data: fallback(), live: false };
  }
}
