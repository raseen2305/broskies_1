// Analytics Types
export interface OverallBreakdown {
  score: number;
  grade: string; // A+, A, B+, B, C+, C, D, F
  description: string;
  calculation?: {
    flagship_weight: number;
    significant_weight: number;
    flagship_average: number;
    significant_average: number;
  };
}

export interface ACIDComponent {
  score: number;
  grade: string;
  description: string;
  flagship: number;
  significant: number;
}

export interface ACIDBreakdown {
  overall: number;
  grade: string;
  components: {
    atomicity: ACIDComponent;
    consistency: ACIDComponent;
    isolation: ACIDComponent;
    durability: ACIDComponent;
  };
}

export interface RepositoryBreakdown {
  total: number;
  flagship: {
    count: number;
    average_score: number;
    average_importance: number;
  };
  significant: {
    count: number;
    average_score: number;
    average_importance: number;
  };
  supporting: {
    count: number;
    average_importance: number;
  };
}

export interface ComplexityBreakdown {
  average_cyclomatic: number;
  average_cognitive: number;
  average_maintainability: number;
  cyclomatic_grade: string;
  maintainability_grade: string;
  total_lines: number;
  total_functions: number;
  total_classes: number;
  repositories_analyzed: number;
}

export interface AnalyticsOverview {
  user_id: string;
  github_username: string;
  overall: OverallBreakdown;
  acid: ACIDBreakdown;
  repositories: RepositoryBreakdown;
  complexity: ComplexityBreakdown;
}

export interface Insight {
  type: 'strength' | 'improvement';
  category: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

export interface Recommendation {
  repository_id: string;
  repository_name: string;
  action: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  difficulty: 'easy' | 'medium' | 'hard';
  estimated_score_increase: number;
}

export interface UserInsights {
  strengths: Insight[];
  improvements: Insight[];
}

export interface UserRecommendations {
  user_id: string;
  recommendations: Recommendation[];
  total: number;
}

export interface RepositoryAnalytics {
  repository_id: string;
  repository_name: string;
  category: string;
  importance_score: number;
  overall_score: number;
  acid_scores: {
    atomicity: number;
    consistency: number;
    isolation: number;
    durability: number;
    overall: number;
  };
  complexity_metrics: {
    cyclomatic_complexity?: number;
    cognitive_complexity?: number;
    maintainability_index?: number;
    total_lines?: number;
    total_functions?: number;
    total_classes?: number;
  };
  insights: Insight[];
  recommendations: Recommendation[];
}
