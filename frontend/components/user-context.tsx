"use client";

// Demo-user context keeps frontend selection separate from backend auth concerns.

import {
  ReactNode,
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";

import { listDemoUsers } from "@/lib/api";
import { DemoUser } from "@/lib/types";

type UserContextValue = {
  users: DemoUser[];
  selectedUser: DemoUser | null;
  setSelectedUserId: (userId: string) => void;
  loading: boolean;
  error: string | null;
};

const UserContext = createContext<UserContextValue | undefined>(undefined);
const STORAGE_KEY = "strugglesense-demo-user";

export function UserProvider({ children }: { children: ReactNode }) {
  const [users, setUsers] = useState<DemoUser[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (saved) {
      setSelectedUserId(saved);
    }
    void listDemoUsers()
      .then((data) => {
        setUsers(data);
        setSelectedUserId((current) => current ?? data[0]?.id ?? null);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Failed to load demo users."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedUserId && typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, selectedUserId);
    }
  }, [selectedUserId]);

  const value = useMemo<UserContextValue>(
    () => ({
      users,
      selectedUser: users.find((user) => user.id === selectedUserId) ?? users[0] ?? null,
      setSelectedUserId,
      loading,
      error
    }),
    [users, selectedUserId, loading, error]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUserContext() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUserContext must be used inside UserProvider.");
  }
  return context;
}
