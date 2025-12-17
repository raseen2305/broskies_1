/**
 * HR Candidates API Service
 * 
 * Provides API methods for HR users to access candidate data, including:
 * - Fetching paginated candidate lists with filters
 * - Getting detailed candidate profiles
 * - Retrieving aggregate insights
 * - Fetching trending languages
 */

import axios, { AxiosInstance } from 'axios';
import { getApiUrl } from '../utils/config';
import { CandidateCardData } from '../components/CandidateCard';

// API base URL
const API_BASE_URL = getApiUrl();

// Types
export interface CandidateQueryParams {
  page?: number;
  limit?: number;
  language?: string;
  min_score?: number;
  max_score?: number;
  role?: string;
  search?: string;
  sort_by?: 'score' | 'upvotes' | 'recent';
}

export interface PaginatedCandidates {
  candidates: CandidateCardData[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ScoredRepository {
  name: string;
  description?: string;
  url: string;
  score: number;
  category: string;
  primary_language: string;
  stars: number;
  forks: number;
  last_updated: string;
}

export interface CandidateProfile {
  username: string;
  full_name?: string;
  bio?: string;
  location?: string;
  profile_picture?: string;
  email?: string;
  github_url: string;
  overall_score: number;
  upvotes: number;
  repositories_count: number;
  total_stars: number;
  total_forks: number;
  language_proficiency: Record<string, number>; // {language: percentage}
  scored_repositories: ScoredRepository[];
  account_created: string;
  last_active: string;
  role_category: string;
}

export interface AggregateInsights {
  total_candidates: number;
  average_score: number;
  top_languages: Array<[string, number]>; // [(language, count)]
  skill_distribution: Record<string, number>; // {level: count}
  top_performers: CandidateCardData[]; // Score >= 8.0
}

export interface TrendingLanguages {
  languages: Array<{
    language: string;
    count: number;
    percentage: number;
    trend: 'up' | 'down' | 'stable';
  }>;
}

// Create axios instance for HR Candidates API
const hrCandidatesApi: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor to add auth token
hrCandidatesApi.interceptors.request.use(
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
hrCandidatesApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      localStorage.removeItem('hr_access_token');
      localStorage.removeItem('hr_refresh_token');
      localStorage.removeItem('hr_user');
      window.location.href = '/hr/auth';
    }
    return Promise.reject(error);
  }
);

/**
 * HR Candidates API Service
 */
export const hrCandidatesApiService = {
  /**
   * Get paginated list of candidates with filters and sorting
   * 
   * @param params - Query parameters for filtering, pagination, and sorting
   * @returns Promise with paginated candidates
   * @throws Error if request fails
   * 
   * @example
   * ```typescript
   * const candidates = await hrCandidatesApiService.getCandidates({
   *   page: 1,
   *   limit: 10,
   *   language: 'JavaScript',
   *   min_score: 7.0,
   *   sort_by: 'score'
   * });
   * ```
   */
  getCandidates: async (params: CandidateQueryParams = {}): Promise<PaginatedCandidates> => {
    try {
      const response = await hrCandidatesApi.get<{success: boolean; data: PaginatedCandidates; message?: string}>(
        '/api/hr/candidates/',
        { params }
      );
      return response.data.data; // Extract data from wrapped response
    } catch (error: any) {
      console.error('Failed to fetch candidates:', error);
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch candidates'
      );
    }
  },

  /**
   * Get detailed profile for a single candidate
   * 
   * @param username - GitHub username of the candidate
   * @returns Promise with complete candidate profile
   * @throws Error if candidate not found or request fails
   * 
   * @example
   * ```typescript
   * const profile = await hrCandidatesApiService.getCandidateDetails('john-doe');
   * console.log('Overall score:', profile.overall_score);
   * ```
   */
  getCandidateDetails: async (username: string): Promise<CandidateProfile> => {
    try {
      const response = await hrCandidatesApi.get<{success: boolean; data: CandidateProfile; message?: string}>(
        `/api/hr/candidates/${username}`
      );
      return response.data.data; // Extract data from wrapped response
    } catch (error: any) {
      console.error('Failed to fetch candidate details:', error);
      
      if (error.response?.status === 404) {
        throw new Error(`Candidate '${username}' not found`);
      }
      
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch candidate details'
      );
    }
  },

  /**
   * Get aggregate insights for the dashboard
   * 
   * @returns Promise with aggregate statistics
   * @throws Error if request fails
   * 
   * @example
   * ```typescript
   * const insights = await hrCandidatesApiService.getAggregateInsights();
   * console.log('Total candidates:', insights.total_candidates);
   * console.log('Average score:', insights.average_score);
   * ```
   */
  getAggregateInsights: async (): Promise<AggregateInsights> => {
    try {
      const response = await hrCandidatesApi.get<{success: boolean; data: AggregateInsights; message?: string}>(
        '/api/hr/candidates/insights/aggregate/'
      );
      return response.data.data; // Extract data from wrapped response
    } catch (error: any) {
      console.error('Failed to fetch aggregate insights:', error);
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch insights'
      );
    }
  },

  /**
   * Get trending programming languages
   * 
   * @returns Promise with trending languages data
   * @throws Error if request fails
   * 
   * @example
   * ```typescript
   * const trending = await hrCandidatesApiService.getTrendingLanguages();
   * trending.languages.forEach(lang => {
   *   console.log(`${lang.language}: ${lang.count} (${lang.trend})`);
   * });
   * ```
   */
  getTrendingLanguages: async (): Promise<TrendingLanguages> => {
    try {
      const response = await hrCandidatesApi.get<{success: boolean; data: TrendingLanguages; message?: string}>(
        '/api/hr/candidates/insights/trending/'
      );
      return response.data.data; // Extract data from wrapped response
    } catch (error: any) {
      console.error('Failed to fetch trending languages:', error);
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch trending languages'
      );
    }
  },

  /**
   * Prefetch candidate profile data for performance optimization
   * 
   * This method initiates a background request to fetch candidate profile data
   * without waiting for the response. Useful for hover prefetching to improve
   * perceived performance when users navigate to profile pages.
   * 
   * @param username - GitHub username of the candidate to prefetch
   * 
   * @example
   * ```typescript
   * // Prefetch on hover
   * onMouseEnter={() => hrCandidatesApiService.prefetchCandidateProfile('john-doe')}
   * ```
   */
  prefetchCandidateProfile: (username: string): void => {
    // Fire and forget - don't wait for response
    hrCandidatesApi.get(`/api/hr/candidates/${username}`)
      .catch(() => {
        // Silently fail - this is just a prefetch optimization
        // Actual error handling will happen when user navigates to the page
      });
  },
};

export default hrCandidatesApiService;
