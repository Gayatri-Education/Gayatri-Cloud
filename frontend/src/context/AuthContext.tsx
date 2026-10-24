'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { UserProfile, OrganizationMembership, ActiveContext } from '../lib/types/auth';
import { api } from '../lib/api-client';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  memberships: OrganizationMembership[];
  activeContext: ActiveContext;
  isLoading: boolean;
  switchOrganization: (organizationId: string | null) => void;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const defaultContext: ActiveContext = {
  organizationId: null,
  organizationName: 'Personal Learning Space',
  role: 'STUDENT',
  isPersonal: true,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [memberships, setMemberships] = useState<OrganizationMembership[]>([]);
  const [activeContext, setActiveContext] = useState<ActiveContext>(defaultContext);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const switchOrganization = (organizationId: string | null) => {
    if (!organizationId) {
      api.setOrganizationId(null);
      setActiveContext(defaultContext);
      return;
    }

    const targetMembership = memberships.find((m) => m.organization_id === organizationId);
    if (targetMembership) {
      api.setOrganizationId(targetMembership.organization_id);
      setActiveContext({
        organizationId: targetMembership.organization_id,
        organizationName: targetMembership.organization_name,
        role: targetMembership.role,
        isPersonal: false,
      });
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await api.getCurrentUser();
      setUser(currentUser);
      const memberList = await api.getMyMemberships();
      setMemberships(memberList || []);

      const savedOrgId = api.getOrganizationId();
      if (savedOrgId && memberList && memberList.length > 0) {
        const found = memberList.find((m) => m.organization_id === savedOrgId);
        if (found) {
          setActiveContext({
            organizationId: found.organization_id,
            organizationName: found.organization_name,
            role: found.role,
            isPersonal: false,
          });
        }
      } else if (memberList && memberList.length > 0) {
        const first = memberList[0];
        api.setOrganizationId(first.organization_id);
        setActiveContext({
          organizationId: first.organization_id,
          organizationName: first.organization_name,
          role: first.role,
          isPersonal: false,
        });
      }
    } catch {
      // Token invalid or network issue
      api.logout();
      setUser(null);
      setToken(null);
      setActiveContext(defaultContext);
    }
  };

  const login = async (email: string, pass: string) => {
    setIsLoading(true);
    try {
      const tokens = await api.login({ email, password: pass });
      setToken(tokens.access_token);
      await refreshUser();
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    api.logout();
    setUser(null);
    setToken(null);
    setMemberships([]);
    setActiveContext(defaultContext);
  };

  useEffect(() => {
    const existingToken = api.getToken();
    if (existingToken) {
      setToken(existingToken);
      refreshUser().finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        memberships,
        activeContext,
        isLoading,
        switchOrganization,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
