"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { User, authApi, setStoredToken, clearStoredToken, getStoredToken } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, role: string, phone?: string) => Promise<void>;
  logout: () => void;
  switchPersona: (role: "donor" | "ngo_admin" | "reviewer" | "volunteer" | "admin") => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize session on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = getStoredToken();
        if (storedToken) {
          try {
            setToken(storedToken);
            const me = await authApi.getMe();
            setUser(me);
            return;
          } catch (tokenErr) {
            console.warn("Stored token expired or invalid, refreshing demo persona...", tokenErr);
            clearStoredToken();
          }
        }
        
        // Default to donor demo persona for immediate seamless hackathon demo experience
        const res = await authApi.switchDemoPersona("donor");
        setStoredToken(res.access_token);
        setToken(res.access_token);
        setUser(res.user);
      } catch (err: any) {
        console.warn("Auth initialization error (Backend unreachable):", err.message);
        clearStoredToken();
        setUser({
          id: "mock-user-id",
          name: "Demo Donor",
          email: "donor@eleos.org",
          role: "donor"
        });
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await authApi.login(email, password);
      setStoredToken(res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (name: string, email: string, password: string, role: string, phone?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await authApi.register(name, email, password, role, phone);
      setStoredToken(res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearStoredToken();
    setUser(null);
    setToken(null);
  };

  const switchPersona = async (role: "donor" | "ngo_admin" | "reviewer" | "volunteer" | "admin") => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await authApi.switchDemoPersona(role);
      setStoredToken(res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    } catch (err: any) {
      console.warn("Backend offline. Switching persona locally:", err.message);
      setUser({
        id: `mock-${role}-id`,
        name: `Demo ${role}`,
        email: `${role}@eleos.org`,
        role: role
      });
      setToken(`mock-token-${role}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        error,
        login,
        register,
        logout,
        switchPersona,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

