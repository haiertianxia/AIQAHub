import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, setAuthToken, clearAuthToken } from "./lib/api";

type UserProfile = {
  id: string;
  email: string;
  name: string;
  status: string;
};

type AuthState = {
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

type LoginResponse = {
  access_token: string;
  token_type: string;
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("aiqahub_token"));
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(token));

  useEffect(() => {
    setAuthToken(token);
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const fetchProfile = async () => {
      try {
        const profile = await api.get<UserProfile>("/auth/me");
        if (!cancelled) {
          setUser(profile);
        }
      } catch {
        if (!cancelled) {
          localStorage.removeItem("aiqahub_token");
          clearAuthToken();
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void fetchProfile();

    return () => {
      cancelled = true;
    };
  }, [token]);

  const value = useMemo<AuthState>(
    () => ({
      user,
      token,
      loading,
      login: async (email: string, password: string) => {
        const response = await api.post<LoginResponse>("/auth/login", { email, password });
        localStorage.setItem("aiqahub_token", response.access_token);
        setToken(response.access_token);
      },
      logout: () => {
        localStorage.removeItem("aiqahub_token");
        clearAuthToken();
        setToken(null);
        setUser(null);
      },
    }),
    [loading, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const state = useContext(AuthContext);
  if (!state) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return state;
}

