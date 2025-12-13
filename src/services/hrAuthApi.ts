/**
 * HR Authentication API Service
 * 
 * Provides API methods for HR user authentication, including:
 * - Google OAuth authorization
 * - OAuth callback handling
 * - User session management
 * - Registration status checking
 * - Logout functionality
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { getApiUrl } from '../utils/config';

// API base URL
const API_BASE_URL = getApiUrl();

// Types
export interface HRUser {
  id: string;
  email: string;
  google_id: string;
  full_name?: string;
  profile_picture?: string;
  company?: string;
  role?: string;
  email_verified: boolean;
  is_approved: boolean;
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

export interface AuthResponse {
  user: HRUser;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface GoogleAuthUrlResponse {
  authorization_url: string;
}

export interface RegistrationStatusResponse {
  email: string;
  approved: boolean;
  registered: boolean;
  message?: string;
}

export interface GoogleCallbackRequest {
  code: string;
  state?: string | null;
}

// Create axios instance for HR API
const hrApi: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor to add auth token
hrApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('hr_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
hrApi.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Handle authentication errors
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('hr_access_token');
      localStorage.removeItem('hr_refresh_token');
      localStorage.removeItem('hr_user');

      // Don't redirect if this is already an auth request
      if (!originalRequest.url?.includes('/auth/hr/')) {
        window.location.href = '/hr/auth';
      }
      return Promise.reject(error);
    }

    // Handle forbidden errors (not approved)
    if (error.response?.status === 403) {
      const errorData = error.response.data as any;
      return Promise.reject({
        ...error,
        message: errorData?.detail || 'Access denied. Please complete registration first.',
      });
    }

    // Handle rate limiting
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      const delay = retryAfter ? parseInt(retryAfter) * 1000 : 60000;

      return Promise.reject({
        ...error,
        message: `Rate limit exceeded. Please try again in ${Math.ceil(delay / 1000)} seconds.`,
        retryAfter: delay,
      });
    }

    // Handle server errors
    if (error.response?.status && error.response.status >= 500) {
      return Promise.reject({
        ...error,
        message: 'Server error. Please try again later.',
      });
    }

    return Promise.reject(error);
  }
);

/**
 * HR Authentication API Service
 */
export const hrAuthApi = {
  /**
   * Get Google OAuth authorization URL
   * 
   * @returns Promise with authorization URL
   * @throws Error if request fails
   * 
   * @example
   * ```typescript
   * const { authorization_url } = await hrAuthApi.getGoogleAuthUrl();
   * window.location.href = authorization_url;
   * ```
   */
  getGoogleAuthUrl: async (): Promise<GoogleAuthUrlResponse> => {
    try {
      const response = await hrApi.get<GoogleAuthUrlResponse>('/auth/hr/google/authorize');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get Google auth URL:', error);
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Failed to get authorization URL'
      );
    }
  },

  /**
   * Handle Google OAuth callback
   * Exchange authorization code for access tokens
   * 
   * @param code - Authorization code from Google
   * @param state - Optional state parameter
   * @returns Promise with user data and tokens
   * @throws Error if authentication fails or user not approved
   * 
   * @example
   * ```typescript
   * const authData = await hrAuthApi.handleGoogleCallback(code);
   * localStorage.setItem('hr_access_token', authData.access_token);
   * ```
   */
  handleGoogleCallback: async (
    code: string,
    state?: string | null
  ): Promise<AuthResponse> => {
    try {
      const response = await hrApi.post<AuthResponse>('/auth/hr/google/callback', {
        code,
        state,
      });
      return response.data;
    } catch (error: any) {
      console.error('Google callback failed:', error);
      
      // Handle specific error cases
      if (error.response?.status === 403) {
        throw new Error(
          'Your email is not approved for access. Please complete the registration form first.'
        );
      }
      
      if (error.response?.status === 400) {
        throw new Error(
          error.response?.data?.detail || 
          'Invalid authorization code. Please try signing in again.'
        );
      }
      
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Authentication failed. Please try again.'
      );
    }
  },

  /**
   * Logout current HR user
   * Invalidates the access token on the server
   * 
   * @returns Promise that resolves when logout is complete
   * @throws Error if logout request fails
   * 
   * @example
   * ```typescript
   * await hrAuthApi.logout();
   * localStorage.clear();
   * navigate('/hr/auth');
   * ```
   */
  logout: async (): Promise<void> => {
    try {
      await hrApi.post('/auth/hr/logout');
    } catch (error: any) {
      console.error('Logout failed:', error);
      // Don't throw error on logout failure - still clear local data
    } finally {
      // Always clear local storage
      localStorage.removeItem('hr_access_token');
      localStorage.removeItem('hr_refresh_token');
      localStorage.removeItem('hr_user');
    }
  },

  /**
   * Get current authenticated HR user information
   * 
   * @returns Promise with current user data
   * @throws Error if not authenticated or request fails
   * 
   * @example
   * ```typescript
   * const user = await hrAuthApi.getCurrentUser();
   * console.log('Logged in as:', user.email);
   * ```
   */
  getCurrentUser: async (): Promise<HRUser> => {
    try {
      const response = await hrApi.get<HRUser>('/auth/hr/me');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get current user:', error);
      
      if (error.response?.status === 401) {
        throw new Error('Not authenticated. Please sign in.');
      }
      
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Failed to get user information'
      );
    }
  },

  /**
   * Check registration status for an email address
   * Verifies if the email is approved for HR dashboard access
   * 
   * @param email - Email address to check
   * @returns Promise with registration status
   * @throws Error if request fails
   * 
   * @example
   * ```typescript
   * const status = await hrAuthApi.checkRegistrationStatus('hr@company.com');
   * if (!status.approved) {
   *   console.log('Please complete registration first');
   * }
   * ```
   */
  checkRegistrationStatus: async (email: string): Promise<RegistrationStatusResponse> => {
    try {
      const response = await hrApi.get<RegistrationStatusResponse>(
        `/auth/hr/registration-status/${encodeURIComponent(email)}`
      );
      return response.data;
    } catch (error: any) {
      console.error('Failed to check registration status:', error);
      
      if (error.response?.status === 404) {
        return {
          email,
          approved: false,
          registered: false,
          message: 'Email not found. Please complete the registration form.',
        };
      }
      
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Failed to check registration status'
      );
    }
  },

  /**
   * Refresh access token using refresh token
   * 
   * @param refreshToken - Refresh token
   * @returns Promise with new tokens
   * @throws Error if refresh fails
   * 
   * @example
   * ```typescript
   * const refreshToken = localStorage.getItem('hr_refresh_token');
   * const newTokens = await hrAuthApi.refreshToken(refreshToken);
   * localStorage.setItem('hr_access_token', newTokens.access_token);
   * ```
   */
  refreshToken: async (refreshToken: string): Promise<AuthResponse> => {
    try {
      const response = await hrApi.post<AuthResponse>('/auth/hr/refresh', {
        refresh_token: refreshToken,
      });
      return response.data;
    } catch (error: any) {
      console.error('Token refresh failed:', error);
      
      // Clear tokens on refresh failure
      localStorage.removeItem('hr_access_token');
      localStorage.removeItem('hr_refresh_token');
      localStorage.removeItem('hr_user');
      
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Session expired. Please sign in again.'
      );
    }
  },

  /**
   * Get Google Form URL for registration
   * 
   * @returns Promise with Google Form URL
   * @throws Error if request fails
   * 
   * @example
   * ```typescript
   * const { form_url } = await hrAuthApi.getGoogleFormUrl();
   * window.open(form_url, '_blank');
   * ```
   */
  getGoogleFormUrl: async (): Promise<{ form_url: string }> => {
    try {
      const response = await hrApi.get<{ form_url: string }>('/auth/hr/form-url');
      return response.data;
    } catch (error: any) {
      console.error('Failed to get Google Form URL:', error);
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Failed to get registration form URL'
      );
    }
  },
};

/**
 * Helper function to get HR access token from localStorage
 */
export const getHRAccessToken = (): string | null => {
  return localStorage.getItem('hr_access_token');
};

/**
 * Helper function to check if HR user is authenticated
 */
export const isHRAuthenticated = (): boolean => {
  return !!localStorage.getItem('hr_access_token');
};

/**
 * Helper function to clear HR authentication data
 */
export const clearHRAuthData = (): void => {
  localStorage.removeItem('hr_access_token');
  localStorage.removeItem('hr_refresh_token');
  localStorage.removeItem('hr_user');
};

export default hrAuthApi;
