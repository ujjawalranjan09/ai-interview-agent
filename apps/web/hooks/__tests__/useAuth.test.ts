import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

const mockSetTokens = vi.fn();

vi.mock("@/stores/authStore", () => ({
  useAuthStore: vi.fn(() => ({
    user: null,
    setUser: vi.fn(),
    setTokens: mockSetTokens,
    logout: vi.fn(),
    isAuthenticated: false,
  })),
}));

vi.mock("@/lib/api", () => ({
  apiFetch: vi.fn(),
  ApiError: class extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe("useAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("login mutation calls apiFetch and sets tokens", async () => {
    const { apiFetch } = await import("@/lib/api");
    const mockLoginResponse = { access_token: "access123", refresh_token: "refresh123" };
    (apiFetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockLoginResponse);

    const { useAuth } = await import("../useAuth");
    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

    result.current.login.mutate({ email: "test@example.com", password: "pass" });

    await waitFor(() => expect(result.current.login.isSuccess).toBe(true));

    expect(apiFetch).toHaveBeenCalledWith("/api/v1/auth/login", {
      method: "POST",
      json: { email: "test@example.com", password: "pass" },
    });
    expect(mockSetTokens).toHaveBeenCalledWith("access123", "refresh123");
  });
});
