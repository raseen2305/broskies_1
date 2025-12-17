// API Types
export interface ScanRequest {
  githubUrl: string;
  scanType: 'myself' | 'others';
  userId: string;
}

export interface ScanResponse {
  scanId: string;
  message: string;
  status?: string;
}

export interface ScanProgress {
  scanId: string;
  status: 'pending' | 'scanning' | 'analyzing' | 'completed' | 'error';
  progress: number;
  currentRepo?: string;
  totalRepos: number;
  message?: string;
  errors?: string[];
  timestamp?: string;
}

export interface GitHubUrlValidation {
  valid: boolean;
  username?: string;
  repository?: string;
  user_info?: GitHubUserInfo | null;
  url_type?: string;
  error?: string;
  suggestion?: string;
  supported_formats?: string[];
  example?: string;
}

export interface GitHubUserInfo {
  login: string;
  name: string | null;
  bio: string | null;
  avatar_url: string;
  public_repos: number;
  followers: number;
  following: number;
  created_at: string;
  updated_at: string;
}

export interface RepositorySearchRequest {
  query: string;
  sort?: string;
  order?: string;
  limit?: number;
}

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  watchers_count: number;
  size: number;
  created_at: string;
  updated_at: string;
  pushed_at: string | null;
  html_url: string;
  clone_url: string;
  topics: string[];
  license: {
    name: string;
    key: string;
  } | null;
}

export interface ScanResults {
  userId: string;
  overallScore: number;
  repositoryCount: number;
  lastScanDate: string | null;
  languages: LanguageStats[];
  techStack: TechStackItem[];
  roadmap: RoadmapItem[];
  repositories?: RepositoryResult[];
  summary?: ScanSummary;
}

export interface LanguageStats {
  language: string;
  percentage: number;
  linesOfCode: number;
  repositories: number;
}

export interface TechStackItem {
  name: string;
  category: string;
  proficiency: number;
  repositories: number;
}

export interface RoadmapItem {
  skill: string;
  currentLevel: number;
  targetLevel: number;
  recommendations: string[];
  priority: 'high' | 'medium' | 'low';
}

export interface RepositoryResult {
  id: string;
  name: string;
  full_name: string;
  description: string | null;
  language: string | null;
  languages: Record<string, number>;
  stars: number;
  forks: number;
  acidScore: number;
  overallScore: number;
  qualityMetrics: QualityMetrics;
  htmlUrl: string;
  analyzedAt: string;
  pullRequestsCount?: number;
  issuesCount?: number;
}

export interface QualityMetrics {
  codeQuality: number;
  documentation: number;
  testing: number;
  security: number;
  maintainability: number;
}

export interface ScanSummary {
  totalRepositories: number;
  totalStars: number;
  totalForks: number;
  primaryLanguages: string[];
  avgScore: number;
  avgAge: number;
  topRepositories: RepositoryResult[];
}

export interface RateLimitInfo {
  core: {
    limit: number;
    remaining: number;
    reset: number;
    used: number;
  };
  search: {
    limit: number;
    remaining: number;
    reset: number;
    used: number;
  };
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string;
  task_id?: string;
  progress?: ScanProgress;
  data?: any;
  timestamp: string;
}

// User Types
export interface User {
  id: string;
  email: string;
  githubUsername?: string;
  githubToken?: string;
  userType: 'developer' | 'hr';
  name?: string;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
}

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  userType: 'developer' | 'hr';
}

// Error Types
export interface APIError {
  detail: string;
  status_code: number;
}

// Component Props Types
export interface DashboardProps {
  user: User;
}

export interface RepositoryScannerProps {
  onScanComplete?: (results: ScanResults) => void;
}

// Hook Types
export interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseScanProgressOptions {
  onComplete?: (scanId: string, progress: ScanProgress) => void;
  onError?: (scanId: string, error: string) => void;
  onProgress?: (scanId: string, progress: ScanProgress) => void;
}

// UI Component Types
export interface Testimonial {
  id: string;
  name: string;
  role: string;
  company: string;
  content: string;
  avatar: string;
  rating: number;
}

// Auth Types
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface DeveloperProfile {
  userId: string;
  overallScore: number;
  repositoryCount: number;
  lastScanDate: string | null;
  languages: LanguageStats[];
  techStack?: TechStackItem[];
  roadmap?: RoadmapItem[];
}

export interface RepositoryEvaluation {
  id: string;
  name: string;
  full_name: string;
  description: string | null;
  language: string | null;
  acidScore: number;
  overallScore: number;
  qualityMetrics: QualityMetrics;
  htmlUrl: string;
  analyzedAt: string;
}

export interface HRRegistration {
  email: string;
  company: string;
  role: string;
  hiring_needs?: string;
}

// Profile and Ranking Types
export interface UserProfile {
  github_username: string;
  full_name: string;
  university: string;
  university_short: string;
  description?: string;
  nationality: string;
  state: string;
  district: string;
  region: string;
}

export interface ProfileSetupRequest {
  github_username: string;
  full_name: string;
  university: string;
  description?: string;
  nationality: string;
  state: string;
  district: string;
}

export interface ProfileResponse {
  profile: UserProfile;
  has_profile: boolean;
}

export interface RankingDetails {
  rank_in_region: number;
  total_users_in_region: number;
  percentile_region: number;
<<<<<<< HEAD
  overall_score?: number;
=======
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
}

export interface UniversityRankingDetails {
  rank_in_university: number;
  total_users_in_university: number;
  percentile_university: number;
<<<<<<< HEAD
  overall_score?: number;
}

export interface UserRankings {
  status?: string; // "available", "pending_profile", "pending_scan", "calculating"
  message?: string; // Status message
  has_complete_profile?: boolean;
  profile_completed?: boolean;
  regional_percentile_text?: string;  // "Top 93% in IN"
  university_percentile_text?: string; // "Top 1% in tce"
  regional_ranking?: RankingDetails | null;
  university_ranking?: UniversityRankingDetails | null;
=======
}

export interface UserRankings {
  regional_percentile_text: string;  // "Top 93% in IN"
  university_percentile_text: string; // "Top 1% in tce"
  regional_ranking: RankingDetails;
  university_ranking: UniversityRankingDetails;
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
}

export interface CountriesResponse {
  countries: string[];
}

export interface StatesResponse {
  states: string[];
}

export interface UniversitiesResponse {
  universities: string[];
}

export interface APIError {
  error: string;
  message: string;
  status_code: number;
}