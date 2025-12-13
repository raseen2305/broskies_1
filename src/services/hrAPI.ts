/**
 * HR API Service
 * 
 * API service for HR-specific endpoints including candidate profile viewing
 */

import axios, { AxiosInstance } from 'axios';
import { getApiUrl } from '../utils/config';

const API_BASE_URL = getApiUrl();

// Create axios instance for HR API calls
const hrAPI: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add HR auth token
hrAPI.interceptors.request.use((config) => {
  const token = localStorage.getItem('hr_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
hrAPI.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle authentication errors
    if (error.response?.status === 401) {
      localStorage.removeItem('hr_access_token');
      localStorage.removeItem('hr_refresh_token');
      localStorage.removeItem('hr_user');
      window.location.href = '/hr/auth';
      return Promise.reject(error);
    }
    
    return Promise.reject(error);
  }
);

// Types
export interface CandidateProfile {
  github_username: string;
  profile: {
    name: string;
    bio: string;
    avatar_url: string;
    location: string;
    company: string;
    email: string;
    blog: string;
    public_repos: number;
    followers: number;
    following: number;
    created_at: string;
    updated_at: string;
  };
  repositories: any[];
  repository_count: number;
  scores: {
    overall_score: number;
    acid_breakdown: {
      activity?: number;
      complexity?: number;
      impact?: number;
      diversity?: number;
    };
  };
  rankings: {
    regional: {
      rank: number;
      total: number;
      percentile: number;
      region: string;
      percentile_text: string;
    };
    university: {
      rank: number;
      total: number;
      percentile: number;
      university: string;
      university_short: string;
      percentile_text: string;
    };
  } | null;
  languages: Array<{ name: string; percentage: number }>;
  tech_stack: string[];
  last_scan_date: string;
  data_age_days: number;
  analyzed: boolean;
  analysis_type: string;
  category_distribution: any;
  comprehensive_data: any;
}

export interface CandidateExistsResponse {
  success: boolean;
  exists: boolean;
  last_scan_date: string | null;
  data_age_days: number | null;
}

export interface CandidateProfileResponse {
  success: boolean;
  candidate: CandidateProfile;
}

/**
 * Get complete candidate profile data
 * 
 * @param username - GitHub username (case-sensitive)
 * @returns Complete candidate profile
 */
export const getCandidateProfile = async (username: string): Promise<CandidateProfile> => {
  try {
    const response = await hrAPI.get<CandidateProfileResponse>(`/api/hr/candidates/${username}`);
    return response.data.candidate;
  } catch (error: any) {
    // Enhanced error handling
    if (error.response?.status === 404) {
      throw new Error(error.response.data?.detail?.message || `Profile not found for ${username}`);
    }
    if (error.response?.status === 500) {
      throw new Error('Unable to load candidate profile. Please try again later.');
    }
    throw new Error(error.response?.data?.detail?.message || 'Failed to fetch candidate profile');
  }
};

/**
 * Check if candidate profile exists
 * 
 * @param username - GitHub username (case-sensitive)
 * @returns Existence status with metadata
 */
export const checkCandidateExists = async (username: string): Promise<CandidateExistsResponse> => {
  try {
    const response = await hrAPI.get<CandidateExistsResponse>(`/api/hr/candidates/${username}/exists`);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail?.message || 'Failed to check candidate existence');
  }
};

export interface RefreshProfileResponse {
  success: boolean;
  message: string;
  username: string;
  scan_initiated: boolean;
}

/**
 * Trigger a fresh scan to refresh candidate profile data
 * 
 * @param username - GitHub username (case-sensitive)
 * @returns Refresh status
 */
export const refreshCandidateProfile = async (username: string): Promise<RefreshProfileResponse> => {
  try {
    const response = await hrAPI.post<RefreshProfileResponse>(`/api/hr/candidates/${username}/refresh`);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail?.message || 'Failed to refresh candidate profile');
  }
};

export default {
  getCandidateProfile,
  checkCandidateExists,
  refreshCandidateProfile,
};
