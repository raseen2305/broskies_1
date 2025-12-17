/**
 * Environment configuration utilities for the GitHub Repository Evaluator
 * Handles API URLs, WebSocket URLs, and environment detection for different deployment platforms
 */

export interface EnvironmentConfig {
  apiUrl: string;
  wsUrl: string;
  environment: 'development' | 'production' | 'staging';
  platform: 'local' | 'vercel' | 'netlify' | 'custom';
}

/**
 * Detect the current deployment platform
 */
export const detectPlatform = (): EnvironmentConfig['platform'] => {
  if (typeof window === 'undefined') {
    return 'local';
  }

  const { hostname } = window.location;
  
  if (hostname.includes('vercel.app') || hostname.includes('.vercel.app')) {
    return 'vercel';
  }
  
  if (hostname.includes('netlify.app') || hostname.includes('.netlify.app')) {
    return 'netlify';
  }
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'local';
  }
  
  return 'custom';
};

/**
 * Detect the current environment
 */
export const detectEnvironment = (): EnvironmentConfig['environment'] => {
  const envVar = (import.meta as any).env?.VITE_ENVIRONMENT;
  if (envVar) {
    return envVar as EnvironmentConfig['environment'];
  }

  const platform = detectPlatform();
  return platform === 'local' ? 'development' : 'production';
};

/**
 * Get the API base URL based on environment and platform
 */
export const getApiUrl = (): string => {
  // Check for explicit environment variable first
  const envApiUrl = (import.meta as any).env?.VITE_API_URL;
  if (envApiUrl) {
    return envApiUrl;
  }

  const platform = detectPlatform();
  
  switch (platform) {
    case 'vercel':
    case 'netlify':
    case 'custom':
      return '/api';  // Use relative API path for deployed environments
    
    case 'local':
    default:
      return 'http://localhost:8000';  // Use localhost for development
  }
};

/**
 * Get the WebSocket URL based on environment and platform
 */
export const getWebSocketUrl = (): string => {
  // Check for explicit environment variable first
  const envWsUrl = (import.meta as any).env?.VITE_WS_URL;
  if (envWsUrl) {
    return envWsUrl;
  }

  if (typeof window === 'undefined') {
    return 'ws://localhost:8000';
  }

  const { hostname, protocol } = window.location;
  const platform = detectPlatform();
  
  switch (platform) {
    case 'vercel':
    case 'netlify':
    case 'custom':
      // Use secure WebSocket for HTTPS, regular WebSocket for HTTP
      const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
      return `${wsProtocol}//${hostname}`;
    
    case 'local':
    default:
      return 'ws://localhost:8000';
  }
};

/**
 * Get complete environment configuration
 */
export const getEnvironmentConfig = (): EnvironmentConfig => {
  return {
    apiUrl: getApiUrl(),
    wsUrl: getWebSocketUrl(),
    environment: detectEnvironment(),
    platform: detectPlatform(),
  };
};

/**
 * Check if running in development mode
 */
export const isDevelopment = (): boolean => {
  return detectEnvironment() === 'development';
};

/**
 * Check if running in production mode
 */
export const isProduction = (): boolean => {
  return detectEnvironment() === 'production';
};

/**
 * Check if running on Vercel
 */
export const isVercel = (): boolean => {
  return detectPlatform() === 'vercel';
};

/**
 * Check if running locally
 */
export const isLocal = (): boolean => {
  return detectPlatform() === 'local';
};

/**
 * Log current configuration (useful for debugging)
 */
export const logEnvironmentConfig = (): void => {
  const config = getEnvironmentConfig();
  console.log('Environment Configuration:', config);
};

// Export the configuration for immediate use
export const config = getEnvironmentConfig();