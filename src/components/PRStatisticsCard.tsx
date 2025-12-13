import React, { useState } from 'react';
import { GitPullRequest, GitMerge, XCircle, Clock, TrendingUp, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Types (Requirements: 2.1, 6.1)
interface PullRequest {
  number: number;
  title: string;
  author: string;
  state: 'open' | 'closed' | 'merged';
  createdAt: string;
  mergedAt?: string;
  url: string;
}

interface PRStatistics {
  total: number;
  open: number;
  closed: number;
  merged: number;
  recent: PullRequest[];
  avgTimeToMerge?: number; // in hours
}

interface PRStatisticsCardProps {
  statistics: PRStatistics;
  repoName?: string;
  onViewAll?: () => void;
  className?: string;
}

const PRStatisticsCard: React.FC<PRStatisticsCardProps> = ({
  statistics,
  repoName,
  onViewAll,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Calculate percentages
  const mergeRate = statistics.total > 0 
    ? Math.round((statistics.merged / statistics.total) * 100) 
    : 0;

  // Format time
  const formatTimeToMerge = (hours?: number) => {
    if (!hours) return 'N/A';
    if (hours < 24) return `${Math.round(hours)}h`;
    const days = Math.round(hours / 24);
    return `${days}d`;
  };

  // Get state color
  const getStateColor = (state: string) => {
    switch (state) {
      case 'open':
        return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400';
      case 'merged':
        return 'text-purple-600 bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400';
      case 'closed':
        return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-400';
    }
  };

  // Get state icon
  const getStateIcon = (state: string) => {
    switch (state) {
      case 'open':
        return <GitPullRequest className="w-4 h-4" />;
      case 'merged':
        return <GitMerge className="w-4 h-4" />;
      case 'closed':
        return <XCircle className="w-4 h-4" />;
      default:
        return <GitPullRequest className="w-4 h-4" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-xl transition-shadow duration-300 ${className}`}
    >
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <GitPullRequest className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Pull Requests
              </h3>
              {repoName && (
                <p className="text-sm text-gray-600 dark:text-gray-400">{repoName}</p>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              {statistics.total}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Total PRs</div>
          </div>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {statistics.open}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Open</div>
          </div>
          <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {statistics.merged}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Merged</div>
          </div>
          <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {statistics.closed}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Closed</div>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="p-6 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Merge Rate</div>
              <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {mergeRate}%
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Avg. Merge Time</div>
              <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {formatTimeToMerge(statistics.avgTimeToMerge)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent PRs */}
      {statistics.recent && statistics.recent.length > 0 && (
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Recent Pull Requests
            </h4>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium transition-colors"
            >
              {isExpanded ? 'Show Less' : 'Show All'}
            </button>
          </div>

          <div className="space-y-3">
            <AnimatePresence>
              {statistics.recent
                .slice(0, isExpanded ? undefined : 3)
                .map((pr, index) => (
                  <motion.div
                    key={pr.number}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-900 transition-colors group"
                  >
                    <div className={`p-1.5 rounded ${getStateColor(pr.state)}`}>
                      {getStateIcon(pr.state)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h5 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
                          {pr.title}
                        </h5>
                        <a
                          href={pr.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-shrink-0 text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
                        <span>#{pr.number}</span>
                        <span>•</span>
                        <span>by {pr.author}</span>
                        <span>•</span>
                        <span>{new Date(pr.createdAt).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </motion.div>
                ))}
            </AnimatePresence>
          </div>

          {onViewAll && statistics.recent.length > 3 && (
            <button
              onClick={onViewAll}
              className="w-full mt-4 py-2 text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors"
            >
              View All {statistics.total} Pull Requests
            </button>
          )}
        </div>
      )}

      {/* Empty State */}
      {(!statistics.recent || statistics.recent.length === 0) && (
        <div className="p-6 text-center">
          <GitPullRequest className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No pull requests found
          </p>
        </div>
      )}
    </motion.div>
  );
};

export default PRStatisticsCard;
