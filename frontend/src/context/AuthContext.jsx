import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [studio, setStudio] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    const token = localStorage.getItem("eh_token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data.user);
      setStudio(data.studio);
    } catch {
      localStorage.removeItem("eh_token");
      setUser(null);
      setStudio(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("eh_token", data.access_token);
    setUser(data.user);
    setStudio(data.studio);
    return data;
  };

  const logout = () => {
    localStorage.removeItem("eh_token");
    setUser(null);
    setStudio(null);
    window.location.href = "/login";
  };

  return (
    <AuthCtx.Provider value={{ user, studio, loading, login, logout, refresh: fetchMe }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
