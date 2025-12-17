import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  GitPullRequest, 
  GitMerge, 
  MessageSquare, 
  Clock, 
  Users, 
  TrendingUp,
  CheckCircle,
  XCircle,
  AlertCircle,
  BarChart3,
  Calendar,
  Target
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface PullRequestAnalysisProps {
  scanResults?: any;
}

interface PRAnalysis {
  summary: {
    total_pull_requests: number;
    merged_pull_requests: number;
    closed_pull_requests: number;
    open_pull_requests: number;
    merge_rate: number;
    repositories_with_prs: number;
  };
  metrics: {
    average_review_time: number;
    average_merge_time: number;
    reviews_per_pr: number;
    comments_per_pr: number;
    lines_changed_per_pr: number;
  };
  collaboration: {
    unique_reviewers: string[];
    frequent_collaborators: Array<{
      username: string;
      collaboration_count: number;
    }>;
    review_participation_rate: number;
  };
  patterns: {
    pr_size_distribution: {
      small: number;
      medium: number;
      large: number;
      xl: number;
    };
    merge_day_patterns: Record<string, number>;
  };
  quality_indicators: {
    prs_with_tests: number;
    prs_with_documentation: number;
    prs_with_multiple_reviewers: number;
    breaking_change_rate: number;
  };
  repository_breakdown: Array<{
    repository_name: string;
    pull_request_count: number;
    merged_count: number;
    authored_count: number;
  }>;
}

const PullRequestAnalysis: React.FC<PullRequestAnalysisProps> = ({ scanResults }) => {
  const { user } = useAuth();
  const [prAnalysis, setPrAnalysis] = useState<PRAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadPRAnalysis = async () => {
      console.log('[PR Analysis] Starting load, scanResults:', scanResults);
      
      // Check for comprehensive PR analysis first (must have summary data)
      const comprehensiveAnalysis = scanResults?.pullRequestAnalysis || scanResults?.comprehensiveData?.pull_request_analysis;
      if (comprehensiveAnalysis && comprehensiveAnalysis.summary && Object.keys(comprehensiveAnalysis.summary).length > 0) {
        console.log('[PR Analysis] Found comprehensive analysis with data:', comprehensiveAnalysis);
        setPrAnalysis(comprehensiveAnalysis);
        setIsLoading(false);
        return;
      }
      
      if (comprehensiveAnalysis) {
        console.log('[PR Analysis] Found comprehensive analysis but it\'s empty:', comprehensiveAnalysis);
      }
      
      // Aggregate PR data from repositories if available
      if (scanResults?.repositories && Array.isArray(scanResults.repositories)) {
        const repos = scanResults.repositories;
        console.log('[PR Analysis] Checking repositories for PR data:', repos.length);
        console.log('[PR Analysis] Sample repo structure:', repos[0]);
        console.log('[PR Analysis] Has pull_requests field?', 'pull_requests' in (repos[0] || {}));
        const reposWithPRs = repos.filter(repo => repo.pull_requests && repo.pull_requests.total > 0);
        console.log('[PR Analysis] Repos with PRs > 0:', reposWithPRs.length);
        
        // Always create analysis, even if no PRs (show zeros)
        if (true) {
          // Aggregate PR statistics
          const totalPRs = reposWithPRs.reduce((sum, repo) => sum + (repo.pull_requests?.total || 0), 0);
          const totalOpen = reposWithPRs.reduce((sum, repo) => sum + (repo.pull_requests?.open || 0), 0);
          const totalClosed = reposWithPRs.reduce((sum, repo) => sum + (repo.pull_requests?.closed || 0), 0);
          const totalMerged = reposWithPRs.reduce((sum, repo) => sum + (repo.pull_requests?.merged || 0), 0);
          
          // Calculate average merge time
          const mergeTimes = reposWithPRs
            .map(repo => repo.pull_requests?.avgTimeToMerge)
            .filter(time => time != null);
          const avgMergeTime = mergeTimes.length > 0 
            ? mergeTimes.reduce((sum, time) => sum + time, 0) / mergeTimes.length 
            : 0;
          
          // Create aggregated analysis
          const aggregatedAnalysis: PRAnalysis = {
            summary: {
              total_pull_requests: totalPRs,
              merged_pull_requests: totalMerged,
              closed_pull_requests: totalClosed,
              open_pull_requests: totalOpen,
              merge_rate: totalPRs > 0 ? (totalMerged / totalPRs) * 100 : 0,
              repositories_with_prs: reposWithPRs.length
            },
            metrics: {
              average_review_time: 0,
              average_merge_time: avgMergeTime,
              reviews_per_pr: 0,
              comments_per_pr: 0,
              lines_changed_per_pr: 0
            },
            collaboration: {
              unique_reviewers: [],
              frequent_collaborators: [],
              review_participation_rate: 0
            },
            patterns: {
              pr_size_distribution: {
                small: 0,
                medium: 0,
                large: 0,
                xl: 0
              },
              merge_day_patterns: {}
            },
            quality_indicators: {
              prs_with_tests: 0,
              prs_with_documentation: 0,
              prs_with_multiple_reviewers: 0,
              breaking_change_rate: 0
            },
            repository_breakdown: reposWithPRs.map(repo => ({
              repository_name: repo.name || repo.full_name || 'Unknown',
              pull_request_count: repo.pull_requests?.total || 0,
              merged_count: repo.pull_requests?.merged || 0,
              authored_count: repo.pull_requests?.total || 0
            }))
          };
          
          console.log('[PR Analysis] Created aggregated analysis:', aggregatedAnalysis);
          setPrAnalysis(aggregatedAnalysis);
          setIsLoading(false);
          return;
        }
      }
      
      console.log('[PR Analysis] No repositories found, creating empty analysis');
      
      // No PR data available - create empty analysis to show UI with zeros
      const emptyAnalysis: PRAnalysis = {
        summary: {
          total_pull_requests: 0,
          merged_pull_requests: 0,
          closed_pull_requests: 0,
          open_pull_requests: 0,
          merge_rate: 0,
          repositories_with_prs: 0
        },
        metrics: {
          average_review_time: 0,
          average_merge_time: 0,
          reviews_per_pr: 0,
          comments_per_pr: 0,
          lines_changed_per_pr: 0
        },
        collaboration: {
          unique_reviewers: [],
          frequent_collaborators: [],
          review_participation_rate: 0
        },
        patterns: {
          pr_size_distribution: {
            small: 0,
            medium: 0,
            large: 0,
            xl: 0
          },
          merge_day_patterns: {}
        },
        quality_indicators: {
          prs_with_tests: 0,
          prs_with_documentation: 0,
          prs_with_multiple_reviewers: 0,
          breaking_change_rate: 0
        },
        repository_breakdown: []
      };
      
      setPrAnalysis(emptyAnalysis);
      setIsLoading(false);
    };

    loadPRAnalysis();
  }, [scanResults]);

  const getSizeColor = (size: string): string => {
    switch (size) {
      case 'small': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'large': return 'bg-orange-100 text-orange-800';
      case 'xl': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTime = (hours: number): string => {
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    if (hours < 24) return `${Math.round(hours)}h`;
    return `${Math.round(hours / 24)}d`;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-8 bg-gray-200 rounded w-64 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-16"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!prAnalysis || !prAnalysis.summary) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Pull Request Analysis</h1>
          <p className="text-gray-600">Collaboration and code review insights</p>
        </div>
        <div className="card p-8 text-center">
          <div className="text-gray-400 mb-4">
            <GitPullRequest className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Loading Pull Request Data</h3>
          <p className="text-gray-600">Analyzing pull request activity...</p>
        </div>
      </div>
    );
  }

  const { summary, metrics, collaboration, patterns, quality_indicators, repository_breakdown } = prAnalysis;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Pull Request Analysis</h1>
        <p className="text-gray-600">
          Collaboration insights from {summary.total_pull_requests} pull requests across {summary.repositories_with_prs} repositories
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-primary-100 rounded-lg p-3">
              <GitPullRequest className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Total PRs</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_pull_requests}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-green-100 rounded-lg p-3">
              <GitMerge className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Merge Rate</p>
              <p className="text-2xl font-bold text-gray-900">{summary.merge_rate}%</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-blue-100 rounded-lg p-3">
              <Clock className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Review Time</p>
              <p className="text-2xl font-bold text-gray-900">{formatTime(metrics.average_review_time)}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-purple-100 rounded-lg p-3">
              <Users className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Collaborators</p>
              <p className="text-2xl font-bold text-gray-900">{collaboration.unique_reviewers.length}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* PR Status Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card p-6"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Pull Request Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center space-x-4">
            <div className="bg-green-50 rounded-full p-3">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">{summary.merged_pull_requests}</p>
              <p className="text-sm text-gray-600">Merged</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="bg-red-50 rounded-full p-3">
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">{summary.closed_pull_requests}</p>
              <p className="text-sm text-gray-600">Closed</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="bg-yellow-50 rounded-full p-3">
              <AlertCircle className="h-8 w-8 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-600">{summary.open_pull_requests}</p>
              <p className="text-sm text-gray-600">Open</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PR Size Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">PR Size Distribution</h3>
          <div className="space-y-4">
            {Object.entries(patterns.pr_size_distribution).map(([size, count]) => (
              <div key={size} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSizeColor(size)}`}>
                    {size.toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-600">
                    {size === 'small' && '≤50 lines'}
                    {size === 'medium' && '51-200 lines'}
                    {size === 'large' && '201-500 lines'}
                    {size === 'xl' && '>500 lines'}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-primary-500 h-2 rounded-full"
                      style={{ width: `${(count / summary.total_pull_requests) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Quality Indicators */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Quality Indicators</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">PRs with Tests</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${(quality_indicators.prs_with_tests / summary.total_pull_requests) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900">{quality_indicators.prs_with_tests}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">PRs with Documentation</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${(quality_indicators.prs_with_documentation / summary.total_pull_requests) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900">{quality_indicators.prs_with_documentation}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Multiple Reviewers</span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-purple-500 h-2 rounded-full"
                    style={{ width: `${(quality_indicators.prs_with_multiple_reviewers / summary.total_pull_requests) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900">{quality_indicators.prs_with_multiple_reviewers}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Breaking Changes</span>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-900">{quality_indicators.breaking_change_rate}%</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Collaboration Insights */}
      {collaboration.frequent_collaborators.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Frequent Collaborators</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {collaboration.frequent_collaborators.slice(0, 6).map((collaborator, index) => (
              <div key={collaborator.username} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {collaborator.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">{collaborator.username}</p>
                  <p className="text-xs text-gray-500">{collaborator.collaboration_count} collaborations</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Repository Breakdown */}
      {repository_breakdown.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Repository Activity</h3>
          <div className="space-y-3">
            {repository_breakdown.slice(0, 10).map((repo, index) => (
              <div key={repo.repository_name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{repo.repository_name}</p>
                  <p className="text-sm text-gray-600">
                    {repo.authored_count} authored • {repo.merged_count} merged
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-primary-600">{repo.pull_request_count}</p>
                  <p className="text-xs text-gray-500">PRs</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Engagement Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
        className="card p-6"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Engagement Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary-600 mb-2">
              {metrics.reviews_per_pr.toFixed(1)}
            </div>
            <p className="text-sm text-gray-600">Reviews per PR</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-secondary-600 mb-2">
              {metrics.comments_per_pr.toFixed(1)}
            </div>
            <p className="text-sm text-gray-600">Comments per PR</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-accent-600 mb-2">
              {collaboration.review_participation_rate}%
            </div>
            <p className="text-sm text-gray-600">Review Participation</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default PullRequestAnalysis;