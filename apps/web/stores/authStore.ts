import { create } from "zustand";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,

  setTokens: (accessToken, refreshToken) => {
    sessionStorage.setItem(
      "auth-tokens",
      JSON.stringify({ accessToken, refreshToken })
    );
    // Set cookie for middleware route protection (7 day expiry)
    document.cookie = `auth-token=${accessToken}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;
    set({ accessToken, refreshToken, isAuthenticated: true });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    sessionStorage.removeItem("auth-tokens");
    document.cookie = "auth-token=; path=/; max-age=0";
    set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    const tokens = sessionStorage.getItem("auth-tokens");
    if (tokens) {
      const parsed = JSON.parse(tokens);
      set({
        accessToken: parsed.accessToken,
        refreshToken: parsed.refreshToken,
        isAuthenticated: true,
      });
    }
  },
}));
