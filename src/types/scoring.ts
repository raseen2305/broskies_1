// Quick Scan Types
export interface QuickScanRequest {
  github_username?: string;
}

export interface RepositorySummary {
  id: string;
  name: string;
  full_name: string;
  description: string | null;
  language: string | null;
  stars: number;
  forks: number;
  importance_score: number;
  category: 'flagship' | 'significant' | 'supporting';
}

export interface QuickScanResponse {
  success: boolean;
  username: string;
  user_profile: {
    login: string;
    name: string | null;
    avatar_url: string;
    public_repos: number;
    followers: number;
    following: number;
    bio?: string | null;
    company?: string | null;
    location?: string | null;
    blog?: string | null;
  };
  repositories: RepositorySummary[];
  summary: {
    flagship: number;
    significant: number;
    supporting: number;
  };
  scan_time: number;
  message: string;
}

// Deep Analysis Types
export interface DeepAnalysisRequest {
  max_repositories?: number; // 1-15, default 15
}

export interface DeepAnalysisResponse {
  success: boolean;
  analysis_id: string;
  user_id: string;
  message: string;
  repositories_selected: number;
  estimated_time: string;
}

export interface AnalysisProgress {
  analysis_id: string;
  user_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress_percentage: number;
  current_repository: string | null;
  repositories_completed: number;
  total_repositories: number;
  estimated_completion: string | null;
  message: string | null;
  error: string | null;
}

export interface AnalysisResults {
  success: boolean;
  user_id: string;
  overall_score: number;
  flagship_average: number;
  significant_average: number;
  repositories_analyzed: number;
  flagship_count: number;
  significant_count: number;
  analysis_completed_at: string;
}

export interface ScanStatus {
  scanned: boolean;
  scanned_at?: string;
  repository_count: number;
  flagship_count: number;
  significant_count: number;
  supporting_count: number;
  message?: string;
}
