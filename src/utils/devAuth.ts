/**
 * Development Authentication Utilities
 * 
 * SECURITY WARNING: This file is for DEVELOPMENT/TESTING ONLY
 * Remove or disable before production deployment
 */

import { HRUser } from '../services/hrAuthApi';

// Development mode flag
const isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development';

// Secure test credentials (hashed in production, plain for dev)
const DEV_CREDENTIALS = {
  email: 'test.hr@example.com',
  password: 'DevTest2024!Secure', // Change this to your secure password
};

// Mock HR user for testing
const MOCK_HR_USER: HRUser = {
  id: 'dev-test-user-001',
  email: DEV_CREDENTIALS.email,
  google_id: 'dev-google-id-001',
  full_name: 'Test HR Manager',
  profile_picture: undefined,
  company: 'Development Testing Inc.',
  role: 'Senior HR Manager',
  email_verified: true,
  is_approved: true,
  created_at: new Date().toISOString(),
  last_login: new Date().toISOString(),
  is_active: true,
};

// Mock tokens
const MOCK_ACCESS_TOKEN = 'dev-mock-access-token-' + Date.now();
const MOCK_REFRESH_TOKEN = 'dev-mock-refresh-token-' + Date.now();

/**
 * Check if development login is enabled
 */
export const isDevLoginEnabled = (): boolean => {
  return isDevelopment && import.meta.env.VITE_ENABLE_DEV_LOGIN === 'true';
};

/**
 * Validate development credentials
 */
export const validateDevCredentials = (email: string, password: string): boolean => {
  if (!isDevLoginEnabled()) {
    console.warn('Development login is not enabled');
    return false;
  }

  return email === DEV_CREDENTIALS.email && password === DEV_CREDENTIALS.password;
};

/**
 * Perform development login (calls backend endpoint)
 */
export const performDevLogin = async (email: string, password: string): Promise<{
  success: boolean;
  user?: HRUser;
  access_token?: string;
  refresh_token?: string;
  error?: string;
}> => {
  if (!isDevLoginEnabled()) {
    return {
      success: false,
      error: 'Development login is not enabled',
    };
  }

  if (!validateDevCredentials(email, password)) {
    return {
      success: false,
      error: 'Invalid credentials',
    };
  }

  try {
    // Call backend dev login endpoint
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/auth/hr/dev/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return {
        success: false,
        error: errorData.detail || 'Development login failed',
      };
    }

    const data = await response.json();

    // Store tokens in localStorage
    localStorage.setItem('hr_access_token', data.access_token);
    localStorage.setItem('hr_refresh_token', data.refresh_token);
    localStorage.setItem('hr_user', JSON.stringify(data.user));

    console.log('✅ Development login successful');

    // Dispatch custom event to notify HRAuthContext
    window.dispatchEvent(new Event('hr-auth-changed'));

    return {
      success: true,
      user: data.user,
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    };
  } catch (error) {
    console.error('Development login error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Development login failed',
    };
  }
};

/**
 * Get development credentials (for display in UI)
 */
export const getDevCredentials = (): { email: string; password: string } | null => {
  if (!isDevLoginEnabled()) {
    return null;
  }

  return DEV_CREDENTIALS;
};

/**
 * Check if current session is a dev session
 */
export const isDevSession = (): boolean => {
  const token = localStorage.getItem('hr_access_token');
  return token?.startsWith('dev-mock-access-token-') || false;
};

export default {
  isDevLoginEnabled,
  validateDevCredentials,
  performDevLogin,
  getDevCredentials,
  isDevSession,
};
