/**
 * Test Authentication Utilities for Development
 * 
 * WARNING: This is for DEVELOPMENT/TESTING ONLY
 * Remove before production deployment
 */

// Check if we're in development mode
const isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development';

/**
 * Create a test authentication token for development
 * This simulates a logged-in developer user
 */
export const createTestAuthToken = (userId: string = 'test-user-123', username: string = 'testuser'): void => {
  if (!isDevelopment) {
    console.warn('Test authentication is only available in development mode');
    return;
  }

  // Create a mock JWT-like token (this won't work with real JWT verification)
  // In a real scenario, you'd get this from your backend auth endpoint
  const mockToken = `test-token-${userId}-${Date.now()}`;
  
  // Store in localStorage (same key that api.ts uses)
  localStorage.setItem('auth_token', mockToken);
  
  // Also store user info
  const mockUser = {
    id: userId,
    username: username,
    email: `${username}@test.com`,
    user_type: 'developer'
  };
  
  localStorage.setItem('auth_user', JSON.stringify(mockUser));
  
  console.log('✅ Test authentication token created');
  console.log('🔄 Please refresh the page to apply authentication');
};

/**
 * Clear test authentication
 */
export const clearTestAuth = (): void => {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  console.log('🗑️ Test authentication cleared');
};

/**
 * Check if user has any auth token
 */
export const hasAuthToken = (): boolean => {
  return !!(
    localStorage.getItem('auth_token') || 
    localStorage.getItem('hr_access_token') ||
    localStorage.getItem('token')
  );
};

/**
 * Get current auth status
 */
export const getAuthStatus = (): { 
  hasToken: boolean; 
  tokenType: string | null; 
  userId: string | null; 
} => {
  const authToken = localStorage.getItem('auth_token');
  const hrToken = localStorage.getItem('hr_access_token');
  const legacyToken = localStorage.getItem('token');
  
  if (authToken) {
    const user = JSON.parse(localStorage.getItem('auth_user') || '{}');
    return { hasToken: true, tokenType: 'developer', userId: user.id || null };
  }
  
  if (hrToken) {
    const user = JSON.parse(localStorage.getItem('hr_user') || '{}');
    return { hasToken: true, tokenType: 'hr', userId: user.id || null };
  }
  
  if (legacyToken) {
    return { hasToken: true, tokenType: 'legacy', userId: null };
  }
  
  return { hasToken: false, tokenType: null, userId: null };
};

// Export for console access in development
if (isDevelopment) {
  (window as any).testAuth = {
    createTestAuthToken,
    clearTestAuth,
    hasAuthToken,
    getAuthStatus
  };
  
  console.log('🔧 Test auth utilities available at window.testAuth');
  console.log('📝 Usage: testAuth.createTestAuthToken("your-user-id", "your-username")');
}