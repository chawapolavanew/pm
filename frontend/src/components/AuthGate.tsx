"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginPage } from "@/components/LoginPage";
import {
  clearToken,
  getToken,
  loginRequest,
  logoutRequest,
  setToken,
} from "@/lib/auth";

export const AuthGate = () => {
  const [token, setTokenState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setTokenState(getToken());
    setReady(true);
  }, []);

  const handleLogin = async (username: string, password: string) => {
    const t = await loginRequest(username, password);
    setToken(t);
    setTokenState(t);
  };

  const handleLogout = async () => {
    if (token) await logoutRequest(token);
    clearToken();
    setTokenState(null);
  };

  if (!ready) return null;
  if (!token) return <LoginPage onLogin={handleLogin} />;
  return <KanbanBoard onLogout={handleLogout} />;
};
