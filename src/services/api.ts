import axios from 'axios';
import { AuthResponse, ScanProgress, DeveloperProfile, RepositoryEvaluation, HRRegistration } from '../types';
import { 
  QuickScanRequest, 
  QuickScanResponse, 
  DeepAnalysisRequest, 
  DeepAnalysisResponse, 
  AnalysisProgress, 
  AnalysisResults,
  ScanStatus 
} from '../types/scoring';
import { 
  AnalyticsOverview, 
  RepositoryAnalytics, 
  UserInsights, 
  UserRecommendations 
} from '../types/analytics';
import { getApiUrl } from '../utils/config';

const API_BASE_URL = getApiUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Enhanced response interceptor for error handling and retry logic
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle authentication errors
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      
      // Don't redirect if this is already an auth request
      if (!originalRequest.url?.includes('/auth/')) {
        window.location.href = '/';
      }
      return Promise.reject(error);
    }
    
    // Handle rate limiting with retry
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      const delay = retryAfter ? parseInt(retryAfter) * 1000 : 60000; // Default 1 minute
      
      // Only retry if not already retried
      if (!originalRequest._retry) {
        originalRequest._retry = true;
        
        console.log(`Rate limited. Retrying after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        return api(originalRequest);
      }
    }
    
    // Handle server errors with retry for GET requests
    if (error.response?.status >= 500 && originalRequest.method?.toLowerCase() === 'get') {
      if (!originalRequest._retryCount) {
        originalRequest._retryCount = 0;
      }
      
      if (originalRequest._retryCount < 3) {
        originalRequest._retryCount++;
        const delay = Math.pow(2, originalRequest._retryCount) * 1000; // Exponential backoff
        
        console.log(`Server error. Retrying attempt ${originalRequest._retryCount} after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        return api(originalRequest);
      }
    }
    
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  getGitHubAuthUrl: async (): Promise<{ authorization_url: string }> => {
    const response = await api.get('/auth/github/authorize');
    return response.data;
  },

  githubCallback: async (data: { code: string; state: string | null }): Promise<AuthResponse> => {
    const response = await api.get(`/auth/github/callback?code=${data.code}&state=${data.state || ''}`);
    return response.data;
  },

  developerLogin: async (githubToken: string): Promise<AuthResponse> => {
    const response = await api.post('/auth/developer/login', { github_token: githubToken });
    return response.data;
  },

  hrRegister: async (formData: HRRegistration): Promise<AuthResponse> => {
    const response = await api.post('/auth/hr/register', formData);
    return response.data;
  },

  refreshToken: async (refreshToken: string): Promise<AuthResponse> => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  getCurrentUser: async (): Promise<any> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  getSession: async (sessionId: string): Promise<AuthResponse> => {
    const response = await api.get(`/auth/session/${sessionId}`);
    return response.data;
  },

  getGoogleAuthUrl: async (): Promise<{ authorization_url: string }> => {
    const response = await api.get('/auth/google/authorize');
    return response.data;
  },

  googleCompleteRegistration: async (
    oauthData: { code: string; state: string | null },
    registrationData: { company: string; role: string; hiring_needs?: string }
  ): Promise<AuthResponse> => {
    const response = await api.post('/auth/google/complete-registration', {
      ...oauthData,
      ...registrationData
    });
    return response.data;
  },

  getGoogleFormUrl: async (): Promise<{ form_url: string }> => {
    const response = await api.get('/auth/google/form');
    return response.data;
  },
};

// Scanning API
export const scanAPI = {
  scanRepositories: async (request: { github_url: string; scan_type: string }): Promise<{ scanId: string }> => {
    const response = await api.post('/scan/repositories', request);
    return response.data;
  },

  getScanProgress: async (scanId: string): Promise<ScanProgress> => {
    const response = await api.get(`/scan/progress/${scanId}`);
    return response.data;
  },

  getScanResults: async (userId: string): Promise<DeveloperProfile> => {
    // Check if this looks like a MongoDB ObjectId (authenticated user)
    const isObjectId = userId.match(/^[0-9a-f]{24}$/);
    const isExternalFormat = userId.includes('external_');
    
    // For authenticated users (ObjectId format), try authenticated endpoint first
    if (isObjectId && !isExternalFormat) {
      try {
        const response = await api.get(`/scan/results/${userId}`);
        return response.data;
      } catch (error: any) {
        console.error('Authenticated scan results failed:', error);
        
        // For 422 errors, try external results as fallback
        if (error.response?.status === 422) {
          console.log('Authentication failed, trying external results...');
          try {
            const response = await api.get(`/scan/external-results/${userId}`);
            return response.data;
          } catch (externalError: any) {
            console.warn('External results also failed:', externalError);
            throw new Error('Unable to load scan results. Please try logging in again or contact support.');
          }
        } else if (error.response?.status === 401) {
          throw new Error('Authentication failed. Please log in again.');
        } else if (error.response?.status === 403) {
          throw new Error('Access denied. You can only view your own scan results.');
        }
        
        // Re-throw with better error message
        throw new Error(error.response?.data?.detail || 'Failed to load scan results. Please try again.');
      }
    }
    
    // For usernames or external format, use external results endpoint
    try {
      const response = await api.get(`/scan/external-results/${userId}`);
      return response.data;
    } catch (externalError: any) {
      console.warn('External results failed:', externalError);
      
      // Provide specific error message for external results
      if (externalError.response?.status === 404) {
        throw new Error(`No scan results found for user '${userId}'. Please scan this user first.`);
      }
      
      throw new Error(externalError.response?.data?.detail || 'Failed to load external scan results.');
    }
  },

  validateGitHubUrl: async (url: string): Promise<{
    valid: boolean;
    username?: string;
    repository?: string;
    user_info?: any;
    url_type?: string;
    error?: string;
    suggestion?: string;
    supported_formats?: string[];
    example?: string;
  }> => {
    try {
      // Try public validation endpoint first (no auth required)
      const response = await api.post('/scan/validate-github-url-public', { url });
      return response.data;
    } catch (error) {
      // Fallback to authenticated endpoint if available
      try {
        const response = await api.post('/scan/validate-github-url', { url });
        return response.data;
      } catch (authError) {
        // Return error response if both fail
        return {
          valid: false,
          error: 'Unable to validate GitHub URL',
          suggestion: 'Please check the URL format and try again'
        };
      }
    }
  },

  searchRepositories: async (query: string, sort = 'stars', order = 'desc', limit = 30): Promise<{
    query: string;
    total_results: number;
    repositories: any[];
  }> => {
    const response = await api.post('/scan/search-repositories', {
      query,
      sort,
      order,
      limit
    });
    return response.data;
  },

  getRateLimitStatus: async (): Promise<any> => {
    const response = await api.get('/scan/rate-limit');
    return response.data;
  },

  getRepositoryAnalysis: async (owner: string, repo: string): Promise<{
    repository: string;
    analysis: any;
    analyzed_at: string;
  }> => {
    const response = await api.get(`/scan/repository-analysis/${owner}/${repo}`);
    return response.data;
  },

  getUserInfo: async (username: string): Promise<any> => {
    const response = await api.get(`/api/scan/quick-scan/${username}`);
    return response.data.data; // New endpoint wraps data in a 'data' field
  },

  getUserRepositories: async (userId: string): Promise<{ repositories: any[] }> => {
    // If userId looks like a username, format it for external endpoint
    let externalUserId = userId;
    if (userId && !userId.startsWith('external_') && !userId.match(/^[0-9a-f]{24}$/)) {
      externalUserId = `external_${userId}`;
    }
    
    // Try external repositories endpoint first (no authentication required)
    try {
      const response = await api.get(`/scan/external-repositories/${externalUserId}`);
      return response.data;
    } catch (error) {
      // Fallback to authenticated endpoint if external fails
      const response = await api.get(`/scan/repositories/${userId}`);
      return response.data;
    }
  },

  scanExternalUser: async (username: string, forceRefresh: boolean = false): Promise<any> => {
    // Use new quick_scan endpoint (faster, with categorization)
    console.log('🔄 ========================================');
    console.log(`🔄 [FRONTEND] Using QUICK_SCAN endpoint`);
    console.log(`🔄 [FRONTEND] Endpoint: GET /api/scan/quick-scan/${username}`);
    console.log(`🔄 [FRONTEND] Force refresh: ${forceRefresh}`);
    console.log('🔄 ========================================');
    
    try {
      const response = await api.get(`/api/scan/quick-scan/${username}`, {
        params: { force_refresh: forceRefresh }
      });
      console.log('✅ ========================================');
      console.log(`✅ [FRONTEND] Quick scan successful for ${username}`);
      console.log(`✅ [FRONTEND] Response status: ${response.status}`);
      console.log(`✅ [FRONTEND] Response data:`, response.data);
      console.log('✅ ========================================');
      return response.data;
    } catch (error: any) {
      console.error('❌ ========================================');
      console.error(`❌ [FRONTEND] Quick scan failed for ${username}`);
      console.error(`❌ [FRONTEND] Error:`, error);
      if (error.response) {
        console.error(`❌ [FRONTEND] Status: ${error.response.status}`);
        console.error(`❌ [FRONTEND] Response data:`, error.response.data);
        console.error(`❌ [FRONTEND] Headers:`, error.response.headers);
      }
      console.error('❌ ========================================');
      throw error;
    }
  },

  initiateAnalysis: async (username: string, maxEvaluate: number = 15): Promise<{
    analysis_id: string;
    status: string;
    message: string;
    estimated_time: string;
    repositories_count: number;
    max_evaluate: number;
  }> => {
    console.log('🆕 Using NEW optimized deep analysis endpoint');
    const response = await api.post(`/api/analysis/deep-analyze/${username}`, {
      max_repositories: maxEvaluate
    });
    return response.data;
  },

  getAnalysisStatus: async (username: string, analysisId: string): Promise<{
    analysis_id: string;
    status: string;
    current_phase: string;
    progress: {
      total_repos: number;
      scored: number;
      categorized: number;
      evaluated: number;
      to_evaluate: number;
      percentage: number;
      current_message?: string;
    };
    message?: string;
    error?: string;
    created_at: string;
    updated_at: string;
  }> => {
    console.log('🆕 Using NEW optimized progress endpoint');
    const response = await api.get(`/api/analysis/progress/${username}/${analysisId}`);
    return response.data;
  },

  getAnalysisResults: async (username: string, analysisId: string): Promise<{
    username: string;
    repositoryCount: number;
    analyzed: boolean;
    analyzedAt?: string;
    overallScore?: number;
    evaluatedCount: number;
    flagshipCount: number;
    significantCount: number;
    supportingCount: number;
    repositories: any[];
    scoreBreakdown?: any;
  }> => {
    console.log('🆕 Using NEW optimized results endpoint');
    const response = await api.get(`/api/analysis/results/${username}/${analysisId}`);
    return response.data;
  },

  evaluateWithML: async (request: { github_url: string; username: string; ml_endpoint_url?: string }): Promise<any> => {
    const response = await api.post('/scan/evaluate-with-ml', request);
    return response.data;
  },

  setMLEndpoint: async (endpointUrl: string): Promise<any> => {
    const response = await api.post('/scan/configure-ml-endpoint', { ml_endpoint_url: endpointUrl });
    return response.data;
  },

  getMLStatus: async (): Promise<any> => {
    const response = await api.get('/scan/ml-status');
    return response.data;
  },
};

// Evaluation API
export const evaluationAPI = {
  getUserProfile: async (userId: string): Promise<DeveloperProfile> => {
    const response = await api.get(`/evaluation/profile/${userId}`);
    return response.data;
  },

  getRepositoryEvaluations: async (userId: string): Promise<RepositoryEvaluation[]> => {
    const response = await api.get(`/evaluation/repositories/${userId}`);
    return response.data;
  },
};

// Scoring API (New v2.0 endpoints)
export const scoringAPI = {
  quickScan: async (request: QuickScanRequest = {}): Promise<QuickScanResponse> => {
    const response = await api.post('/api/scan/quick-scan', request);
    return response.data;
  },

  getScanStatus: async (userId: string): Promise<ScanStatus> => {
    const response = await api.get(`/api/scan/scan-status/${userId}`);
    return response.data;
  },

  deepAnalyze: async (request: DeepAnalysisRequest = {}): Promise<DeepAnalysisResponse> => {
    const response = await api.post('/api/analysis/deep-analyze', request);
    return response.data;
  },

  getAnalysisProgress: async (userId: string): Promise<AnalysisProgress> => {
    const response = await api.get(`/api/analysis/progress/${userId}`);
    return response.data;
  },

  getAnalysisResults: async (userId: string): Promise<AnalysisResults> => {
    const response = await api.get(`/api/analysis/results/${userId}`);
    return response.data;
  },
};

// Analytics API (New v2.0 endpoints)
export const analyticsAPI = {
  getOverview: async (userId: string): Promise<AnalyticsOverview> => {
    const response = await api.get(`/api/analytics/overview/${userId}`);
    return response.data;
  },

  getRepositoryAnalytics: async (repoId: string): Promise<RepositoryAnalytics> => {
    const response = await api.get(`/api/analytics/repository/${repoId}`);
    return response.data;
  },

  getUserInsights: async (userId: string): Promise<UserInsights> => {
    const response = await api.get(`/api/analytics/insights/${userId}`);
    return response.data;
  },

  getUserRecommendations: async (userId: string, limit: number = 10): Promise<UserRecommendations> => {
    const response = await api.get(`/api/analytics/recommendations/${userId}`, {
      params: { limit }
    });
    return response.data;
  },
};

export default api;