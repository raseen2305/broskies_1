import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (user: User, token: string, refreshToken?: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored auth data on app load
    const storedToken = localStorage.getItem('auth_token');
    const storedRefreshToken = localStorage.getItem('refresh_token');
    const storedUser = localStorage.getItem('auth_user');
    
    if (storedToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        setToken(storedToken);
        
        // Set up token refresh
        setupTokenRefresh(storedRefreshToken);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        clearAuthData();
      }
    }
    
    setIsLoading(false);
  }, []);

  const setupTokenRefresh = (refreshToken: string | null) => {
    if (!refreshToken) return;
    
    // Set up automatic token refresh before expiration
    const refreshInterval = setInterval(async () => {
      try {
        const response = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken })
        });
        
        if (response.ok) {
          const data = await response.json();
          setToken(data.token);
          localStorage.setItem('auth_token', data.token);
          localStorage.setItem('refresh_token', data.refresh_token);
        } else {
          // Refresh failed, logout user
          logout();
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        logout();
      }
    }, 25 * 60 * 1000); // Refresh every 25 minutes (tokens expire in 30)
    
    return () => clearInterval(refreshInterval);
  };

  const clearAuthData = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('auth_user');
  };

  const login = (userData: User, authToken: string, refreshToken?: string) => {
    setUser(userData);
    setToken(authToken);
    localStorage.setItem('auth_token', authToken);
    localStorage.setItem('auth_user', JSON.stringify(userData));
    
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
      setupTokenRefresh(refreshToken);
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint to invalidate tokens on server
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.error('Logout request failed:', error);
    }
    
    setUser(null);
    setToken(null);
    clearAuthData();
  };

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!user && !!token,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};