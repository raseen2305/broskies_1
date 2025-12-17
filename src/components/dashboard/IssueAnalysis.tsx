import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  MessageSquare, 
  Tag, 
  Users, 
  TrendingUp,
  Calendar,
  Target,
  BarChart3,
  XCircle,
  Zap
} from 'lucide-react';

interface IssueAnalysisProps {
  scanResults?: any;
}

interface IssueAnalysis {
  summary: {
    total_issues: number;
    open_issues: number;
    closed_issues: number;
    resolution_rate: number;
    repositories_with_issues: number;
    issues_created: number;
    issues_participated: number;
  };
  metrics: {
    average_resolution_time: number;
    average_response_time: number;
    comments_per_issue: number;
    assignees_per_issue: number;
    labels_per_issue: number;
  };
  patterns: {
    issue_types: Record<string, number>;
    priority_distribution: Record<string, number>;
    resolution_day_patterns: Record<string, number>;
    creation_trends: Record<string, number>;
    top_labels: Array<{ label: string; count: number }>;
  };
  collaboration: {
    unique_assignees: string[];
    frequent_collaborators: Array<{
      username: string;
      participation_count: number;
    }>;
    community_engagement_score: number;
  };
  quality_indicators: {
    issues_with_labels: number;
    issues_with_assignees: number;
    issues_with_milestones: number;
    stale_issue_rate: number;
  };
  repository_breakdown: Array<{
    repository_name: string;
    issue_count: number;
    open_count: number;
    closed_count: number;
    created_count: number;
  }>;
}

const IssueAnalysis: React.FC<IssueAnalysisProps> = ({ scanResults }) => {
  const [issueAnalysis, setIssueAnalysis] = useState<IssueAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadIssueAnalysis = async () => {
      console.log('[Issue Analysis] Starting load, scanResults:', scanResults);
      
      // Check for comprehensive issue analysis first (must have summary data)
      const comprehensiveAnalysis = scanResults?.issueAnalysis || scanResults?.comprehensiveData?.issue_analysis;
      if (comprehensiveAnalysis && comprehensiveAnalysis.summary && Object.keys(comprehensiveAnalysis.summary).length > 0) {
        console.log('[Issue Analysis] Found comprehensive analysis with data:', comprehensiveAnalysis);
        setIssueAnalysis(comprehensiveAnalysis);
        setIsLoading(false);
        return;
      }
      
      if (comprehensiveAnalysis) {
        console.log('[Issue Analysis] Found comprehensive analysis but it\'s empty:', comprehensiveAnalysis);
      }
      
      // Aggregate issue data from repositories if available
      if (scanResults?.repositories && Array.isArray(scanResults.repositories)) {
        const repos = scanResults.repositories;
        console.log('[Issue Analysis] Checking repositories for issue data:', repos.length);
        console.log('[Issue Analysis] Sample repo structure:', repos[0]);
        console.log('[Issue Analysis] Has issues field?', 'issues' in (repos[0] || {}));
        const reposWithIssues = repos.filter(repo => repo.issues && repo.issues.total > 0);
        console.log('[Issue Analysis] Repositories with issues:', reposWithIssues.length);
        
        // Always create analysis, even if no issues (show zeros)
        if (true) {
          // Aggregate issue statistics
          const totalIssues = reposWithIssues.reduce((sum, repo) => sum + (repo.issues?.total || 0), 0);
          const totalOpen = reposWithIssues.reduce((sum, repo) => sum + (repo.issues?.open || 0), 0);
          const totalClosed = reposWithIssues.reduce((sum, repo) => sum + (repo.issues?.closed || 0), 0);
          
          // Calculate average close time
          const closeTimes = reposWithIssues
            .map(repo => repo.issues?.avgTimeToClose)
            .filter(time => time != null);
          const avgCloseTime = closeTimes.length > 0 
            ? closeTimes.reduce((sum, time) => sum + time, 0) / closeTimes.length 
            : 0;
          
          // Aggregate labels
          const allLabels: Record<string, number> = {};
          reposWithIssues.forEach(repo => {
            if (repo.issues?.labelsDistribution) {
              Object.entries(repo.issues.labelsDistribution).forEach(([label, count]) => {
                allLabels[label] = (allLabels[label] || 0) + (count as number);
              });
            }
          });
          
          const topLabels = Object.entries(allLabels)
            .map(([label, count]) => ({ label, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 10);
          
          // Create aggregated analysis
          const aggregatedAnalysis: IssueAnalysis = {
            summary: {
              total_issues: totalIssues,
              open_issues: totalOpen,
              closed_issues: totalClosed,
              resolution_rate: totalIssues > 0 ? (totalClosed / totalIssues) * 100 : 0,
              repositories_with_issues: reposWithIssues.length,
              issues_created: totalIssues,
              issues_participated: totalIssues
            },
            metrics: {
              average_resolution_time: avgCloseTime,
              average_response_time: 0,
              comments_per_issue: 0,
              assignees_per_issue: 0,
              labels_per_issue: topLabels.length > 0 ? topLabels.reduce((sum, l) => sum + l.count, 0) / totalIssues : 0
            },
            patterns: {
              issue_types: {},
              priority_distribution: {},
              resolution_day_patterns: {},
              creation_trends: {},
              top_labels: topLabels
            },
            collaboration: {
              unique_assignees: [],
              frequent_collaborators: [],
              community_engagement_score: 0
            },
            quality_indicators: {
              issues_with_labels: 0,
              issues_with_assignees: 0,
              issues_with_milestones: 0,
              stale_issue_rate: 0
            },
            repository_breakdown: reposWithIssues.map(repo => ({
              repository_name: repo.name || repo.full_name || 'Unknown',
              issue_count: repo.issues?.total || 0,
              open_count: repo.issues?.open || 0,
              closed_count: repo.issues?.closed || 0,
              created_count: repo.issues?.total || 0
            }))
          };
          
          setIssueAnalysis(aggregatedAnalysis);
          setIsLoading(false);
          return;
        }
      }
      
      // No issue data available - create empty analysis to show UI with zeros
      const emptyAnalysis: IssueAnalysis = {
        summary: {
          total_issues: 0,
          open_issues: 0,
          closed_issues: 0,
          resolution_rate: 0,
          repositories_with_issues: 0
        },
        metrics: {
          average_resolution_time: 0,
          average_response_time: 0,
          issues_per_repository: 0,
          comments_per_issue: 0
        },
        patterns: {
          issue_type_distribution: {
            bug: 0,
            enhancement: 0,
            documentation: 0,
            question: 0,
            other: 0
          },
          priority_distribution: {
            high: 0,
            medium: 0,
            low: 0
          },
          resolution_day_patterns: {}
        },
        quality_indicators: {
          issues_with_labels: 0,
          issues_with_assignees: 0,
          issues_with_milestones: 0,
          stale_issues_rate: 0
        },
        repository_breakdown: []
      };
      
      setIssueAnalysis(emptyAnalysis);
      setIsLoading(false);
    };

    loadIssueAnalysis();
  }, [scanResults]);

  const getTypeColor = (type: string): string => {
    switch (type) {
      case 'bug': return 'bg-red-100 text-red-800';
      case 'enhancement': return 'bg-blue-100 text-blue-800';
      case 'documentation': return 'bg-green-100 text-green-800';
      case 'question': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
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

  if (!issueAnalysis || !issueAnalysis.summary) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Issue Analysis</h1>
          <p className="text-gray-600">Issue tracking and resolution insights</p>
        </div>
        <div className="card p-8 text-center">
          <div className="text-gray-400 mb-4">
            <AlertCircle className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Loading Issue Data</h3>
          <p className="text-gray-600">Analyzing issue tracking activity...</p>
        </div>
      </div>
    );
  }

  const { summary, metrics, patterns, collaboration, quality_indicators, repository_breakdown } = issueAnalysis;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Issue Analysis</h1>
        <p className="text-gray-600">
          Issue tracking insights from {summary.total_issues} issues across {summary.repositories_with_issues} repositories
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
              <AlertCircle className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Total Issues</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_issues}</p>
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
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Resolution Rate</p>
              <p className="text-2xl font-bold text-gray-900">{summary.resolution_rate}%</p>
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
              <p className="text-sm font-medium text-gray-600">Avg Resolution</p>
              <p className="text-2xl font-bold text-gray-900">{formatTime(metrics.average_resolution_time)}</p>
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
              <p className="text-2xl font-bold text-gray-900">{collaboration.unique_assignees.length}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Issue Status Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card p-6"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Issue Status & Participation</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">{summary.closed_issues}</div>
            <p className="text-sm text-gray-600">Closed Issues</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600 mb-2">{summary.open_issues}</div>
            <p className="text-sm text-gray-600">Open Issues</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">{summary.issues_created}</div>
            <p className="text-sm text-gray-600">Created</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">{summary.issues_participated}</div>
            <p className="text-sm text-gray-600">Participated</p>
          </div>
        </div>
      </motion.div>

      {/* Issue Types & Priority */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Issue Types</h3>
          <div className="space-y-4">
            {Object.entries(patterns.issue_types).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(type)}`}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-primary-500 h-2 rounded-full"
                      style={{ width: `${(count / summary.total_issues) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Priority Distribution</h3>
          <div className="space-y-4">
            {Object.entries(patterns.priority_distribution).map(([priority, count]) => (
              <div key={priority} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(priority)}`}>
                    {priority.charAt(0).toUpperCase() + priority.slice(1)}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-secondary-500 h-2 rounded-full"
                      style={{ width: `${(count / summary.total_issues) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Quality Indicators */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="card p-6"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Quality Indicators</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600 mb-2">
              {Math.round((quality_indicators.issues_with_labels / summary.total_issues) * 100)}%
            </div>
            <p className="text-sm text-gray-600">With Labels</p>
            <p className="text-xs text-gray-500">{quality_indicators.issues_with_labels} issues</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600 mb-2">
              {Math.round((quality_indicators.issues_with_assignees / summary.total_issues) * 100)}%
            </div>
            <p className="text-sm text-gray-600">With Assignees</p>
            <p className="text-xs text-gray-500">{quality_indicators.issues_with_assignees} issues</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600 mb-2">
              {Math.round((quality_indicators.issues_with_milestones / summary.total_issues) * 100)}%
            </div>
            <p className="text-sm text-gray-600">With Milestones</p>
            <p className="text-xs text-gray-500">{quality_indicators.issues_with_milestones} issues</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600 mb-2">
              {quality_indicators.stale_issue_rate}%
            </div>
            <p className="text-sm text-gray-600">Stale Issues</p>
            <p className="text-xs text-gray-500">90+ days inactive</p>
          </div>
        </div>
      </motion.div>

      {/* Top Labels */}
      {patterns.top_labels.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Most Used Labels</h3>
          <div className="flex flex-wrap gap-2">
            {patterns.top_labels.slice(0, 15).map((labelData, index) => (
              <span
                key={labelData.label}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-800"
              >
                <Tag className="h-3 w-3 mr-1" />
                {labelData.label}
                <span className="ml-2 text-xs bg-gray-200 px-2 py-0.5 rounded-full">
                  {labelData.count}
                </span>
              </span>
            ))}
          </div>
        </motion.div>
      )}

      {/* Collaboration Insights */}
      {collaboration.frequent_collaborators.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
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
                  <p className="text-xs text-gray-500">{collaborator.participation_count} participations</p>
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
          transition={{ delay: 1.0 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Repository Activity</h3>
          <div className="space-y-3">
            {repository_breakdown.slice(0, 10).map((repo, index) => (
              <div key={repo.repository_name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{repo.repository_name}</p>
                  <p className="text-sm text-gray-600">
                    {repo.created_count} created • {repo.open_count} open • {repo.closed_count} closed
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-primary-600">{repo.issue_count}</p>
                  <p className="text-xs text-gray-500">Issues</p>
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
        transition={{ delay: 1.1 }}
        className="card p-6"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Engagement Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary-600 mb-2">
              {formatTime(metrics.average_response_time)}
            </div>
            <p className="text-sm text-gray-600">Avg Response Time</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-secondary-600 mb-2">
              {metrics.comments_per_issue.toFixed(1)}
            </div>
            <p className="text-sm text-gray-600">Comments per Issue</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-accent-600 mb-2">
              {metrics.labels_per_issue.toFixed(1)}
            </div>
            <p className="text-sm text-gray-600">Labels per Issue</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-success-600 mb-2">
              {collaboration.community_engagement_score}%
            </div>
            <p className="text-sm text-gray-600">Community Engagement</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default IssueAnalysis;