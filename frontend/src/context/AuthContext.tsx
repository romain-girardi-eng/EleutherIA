import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import Cookies from 'js-cookie';
import { apiClient } from '../api/client';

export interface User {
  username: string;
  email: string;
  role: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_COOKIE = 'auth_token';
const TOKEN_EXPIRY_DAYS = 7;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Initialize auth state from cookie
  useEffect(() => {
    const initializeAuth = async () => {
      const token = Cookies.get(TOKEN_COOKIE);
      
      if (token) {
        try {
          // Verify token and get user info
          const user = await apiClient.getCurrentUser();
          setState({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Token is invalid, clear it
          console.error('Invalid token:', error);
          Cookies.remove(TOKEN_COOKIE);
          setState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } else {
        setState({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await apiClient.login(credentials);
      
      // Store token in cookie
      Cookies.set(TOKEN_COOKIE, response.access_token, { 
        expires: TOKEN_EXPIRY_DAYS,
        secure: import.meta.env.PROD,
        sameSite: 'strict'
      });

      // Get user info
      const user = await apiClient.getCurrentUser();
      
      setState({
        user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    Cookies.remove(TOKEN_COOKIE);
    setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  const refreshUser = async () => {
    if (!state.token) return;
    
    try {
      const user = await apiClient.getCurrentUser();
      setState(prev => ({
        ...prev,
        user,
      }));
    } catch (error) {
      console.error('Failed to refresh user:', error);
      logout();
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
