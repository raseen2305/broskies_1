import api from './api';
import { ApiWrapper } from './apiWrapper';
import { 
  ProfileSetupRequest, 
  ProfileResponse, 
  UserRankings, 
  CountriesResponse, 
  StatesResponse, 
  UniversitiesResponse,
  APIError 
} from '../types';

const apiWrapper = ApiWrapper.getInstance();

// Profile API service functions
export const profileAPI = {
  // Profile management
  setupProfile: async (data: ProfileSetupRequest): Promise<ProfileResponse> => {
    try {
      const response = await api.post('/profile/setup', data);
      return response.data;
    } catch (error: any) {
      throw handleAPIError(error);
    }
  },

  getProfile: async (): Promise<ProfileResponse> => {
    try {
      const response = await api.get('/profile/me');
      return response.data;
    } catch (error: any) {
      // If authentication fails, try public endpoint
      if (error.response?.status === 403 || error.response?.status === 401) {
        try {
          const publicResponse = await api.get('/profile/me/public');
          return publicResponse.data;
        } catch (publicError) {
          console.warn('Both authenticated and public profile endpoints failed');
        }
      }
      throw handleAPIError(error);
    }
  },

  updateProfile: async (data: ProfileSetupRequest): Promise<ProfileResponse> => {
    try {
      const response = await api.put('/profile/update', data);
      return response.data;
    } catch (error: any) {
      throw handleAPIError(error);
    }
  },

  // Data endpoints for dropdowns
  getCountries: async (): Promise<CountriesResponse> => {
    try {
      const response = await api.get('/profile/data/countries');
      return response.data;
    } catch (error: any) {
      throw handleAPIError(error);
    }
  },

  getStates: async (country: string): Promise<StatesResponse> => {
    try {
      const response = await api.get(`/profile/data/states?country=${encodeURIComponent(country)}`);
      return response.data;
    } catch (error: any) {
      throw handleAPIError(error);
    }
  },

  getUniversities: async (): Promise<UniversitiesResponse> => {
    try {
      const response = await api.get('/profile/data/universities');
      return response.data;
    } catch (error: any) {
      throw handleAPIError(error);
    }
  },
<<<<<<< HEAD

  getDashboardData: async (): Promise<any> => {
    try {
      const response = await api.get('/profile/dashboard-data');
      return response.data;
    } catch (error: any) {
      throw handleAPIError(error);
    }
  },
=======
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
};

// Ranking API service functions
export const rankingAPI = {
  getRankings: async (): Promise<UserRankings> => {
    try {
      const response = await api.get('/rankings');
      return response.data;
    } catch (error: any) {
      throw handleAPIError(error);
    }
  },

  getRegionalStats: async (): Promise<any> => {
    try {
      const response = await api.get('/rankings/stats/regional');
      return response.data;
    } catch (error: any) {
      throw handleAPIError(error);
    }
  },

  getUniversityStats: async (): Promise<any> => {
    try {
      const response = await api.get('/rankings/stats/university');
      return response.data;
    } catch (error: any) {
      throw handleAPIError(error);
    }
  },

  checkExternalRanking: async (githubUsername: string): Promise<any> => {
    try {
      const response = await api.get(`/rankings/check/${githubUsername}`);
      return response.data;
    } catch (error: any) {
      console.error('Failed to check external ranking:', error);
      return {
        has_ranking_data: false,
        message: 'Failed to fetch ranking data'
      };
    }
  },

  syncScore: async (): Promise<any> => {
    try {
      const response = await api.post('/profile/sync-score');
      return response.data;
    } catch (error: any) {
      // If authentication fails, try public endpoint
      if (error.response?.status === 403 || error.response?.status === 401) {
        try {
          const publicResponse = await api.post('/profile/sync-score/public');
          return publicResponse.data;
        } catch (publicError) {
          console.warn('Both authenticated and public sync endpoints failed');
        }
      }
      throw handleAPIError(error);
    }
  },
};

// Error handling helper
const handleAPIError = (error: any): APIError => {
  if (error.response?.data) {
    return {
      error: error.response.data.error || 'API Error',
      message: error.response.data.message || error.response.data.detail || 'An error occurred',
      status_code: error.response.status || 500,
      detail: error.response.data.detail || error.response.data.message || 'An error occurred'
    };
  }
  
  return {
    error: 'Network Error',
    message: error.message || 'Failed to connect to server',
    status_code: 0,
    detail: error.message || 'Failed to connect to server'
  };
};

// Enhanced retry logic using ApiWrapper
export const withRetry = async <T>(
  apiCall: () => Promise<T>,
  options: {
    maxRetries?: number;
    retryDelay?: number;
    timeout?: number;
    cacheKey?: string;
    cacheDuration?: number;
  } = {}
): Promise<T> => {
  return apiWrapper.executeWithRetry(apiCall, {
    retries: options.maxRetries || 3,
    retryDelay: options.retryDelay || 1000,
    timeout: options.timeout || 30000,
    cacheKey: options.cacheKey,
    cacheDuration: options.cacheDuration || 300000,
    showErrorNotification: true
  });
};