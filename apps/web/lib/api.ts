const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiOptions extends RequestInit {
  json?: unknown;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T = any>(
  path: string,
  options: ApiOptions = {}
): Promise<T> {
  const { json, ...fetchOptions } = options;
  const headers = new Headers(fetchOptions.headers);

  // Add auth token from sessionStorage
  const tokens = sessionStorage.getItem("auth-tokens");
  if (tokens) {
    const parsed = JSON.parse(tokens);
    if (parsed.accessToken) {
      headers.set("Authorization", `Bearer ${parsed.accessToken}`);
    }
  }

  if (json) {
    headers.set("Content-Type", "application/json");
    fetchOptions.body = JSON.stringify(json);
  }

  fetchOptions.headers = headers;

  let response = await fetch(`${API_URL}${path}`, fetchOptions);

  // On 401, try refresh
  if (response.status === 401 && tokens) {
    const parsed = JSON.parse(tokens);
    if (parsed.refreshToken) {
      const refreshResponse = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: parsed.refreshToken }),
      });

      if (refreshResponse.ok) {
        const newTokens = await refreshResponse.json();
        const newStored = {
          accessToken: newTokens.access_token,
          refreshToken: newTokens.refresh_token,
        };
        sessionStorage.setItem("auth-tokens", JSON.stringify(newStored));
        // Update cookie for middleware
        document.cookie = `auth-token=${newStored.accessToken}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;
        headers.set("Authorization", `Bearer ${newStored.accessToken}`);
        response = await fetch(`${API_URL}${path}`, { ...fetchOptions, headers });
      }
    }
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(errorBody.detail || "Request failed", response.status);
  }

  return response.json();
}
