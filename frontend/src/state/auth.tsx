import { createContext, useContext, useMemo, useState } from "react";

import { clearToken, getStoredToken, storeToken } from "../api/client";

type AuthContextValue = {
  token: string | null;
  isAuthenticated: boolean;
  setSession: (token: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      isAuthenticated: Boolean(token),
      setSession: (nextToken: string) => {
        storeToken(nextToken);
        setToken(nextToken);
      },
      logout: () => {
        clearToken();
        setToken(null);
      },
    }),
    [token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return value;
}
