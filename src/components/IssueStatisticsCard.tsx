import React, { useState } from 'react';
import { AlertCircle, CheckCircle, Clock, Tag, ExternalLink, TrendingDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Types (Requirements: 2.2, 6.2)
interface Issue {
  number: number;
  title: string;
  author: string;
  state: 'open' | 'closed';
  labels: string[];
  createdAt: string;
  closedAt?: string;
  url: string;
}

interface IssueStatistics {
  total: number;
  open: number;
  closed: number;
  recent: Issue[];
  avgTimeToClose?: number; // in hours
  labelsDistribution?: Record<string, number>;
}

interface IssueStatisticsCardProps {
  statistics: IssueStatistics;
  repoName?: string;
  onViewAll?: () => void;
  className?: string;
}

const IssueStatisticsCard: React.FC<IssueStatisticsCardProps> = ({
  statistics,
  repoName,
  onViewAll,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showLabels, setShowLabels] = useState(false);

  // Calculate close rate
  const closeRate = statistics.total > 0 
    ? Math.round((statistics.closed / statistics.total) * 100) 
    : 0;

  // Format time
  const formatTimeToClose = (hours?: number) => {
    if (!hours) return 'N/A';
    if (hours < 24) return `${Math.round(hours)}h`;
    const days = Math.round(hours / 24);
    return `${days}d`;
  };

  // Get top labels
  const getTopLabels = () => {
    if (!statistics.labelsDistribution) return [];
    return Object.entries(statistics.labelsDistribution)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);
  };

  // Get label color
  const getLabelColor = (label: string) => {
    const colors = [
      'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    ];
    const hash = label.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[hash % colors.length];
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
            <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
              <AlertCircle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Issues
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
            <div className="text-xs text-gray-500 dark:text-gray-400">Total Issues</div>
          </div>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {statistics.open}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Open</div>
          </div>
          <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
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
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <TrendingDown className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Close Rate</div>
              <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {closeRate}%
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Avg. Close Time</div>
              <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {formatTimeToClose(statistics.avgTimeToClose)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top Labels */}
      {statistics.labelsDistribution && Object.keys(statistics.labelsDistribution).length > 0 && (
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Tag className="w-4 h-4" />
              Top Labels
            </h4>
            <button
              onClick={() => setShowLabels(!showLabels)}
              className="text-sm text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300 font-medium transition-colors"
            >
              {showLabels ? 'Hide' : 'Show All'}
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {getTopLabels()
              .slice(0, showLabels ? undefined : 3)
              .map(([label, count]) => (
                <span
                  key={label}
                  className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getLabelColor(label)}`}
                >
                  {label}
                  <span className="ml-1 px-1.5 py-0.5 bg-white/50 dark:bg-black/20 rounded-full text-xs">
                    {count}
                  </span>
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Recent Issues */}
      {statistics.recent && statistics.recent.length > 0 && (
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Recent Issues
            </h4>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300 font-medium transition-colors"
            >
              {isExpanded ? 'Show Less' : 'Show All'}
            </button>
          </div>

          <div className="space-y-3">
            <AnimatePresence>
              {statistics.recent
                .slice(0, isExpanded ? undefined : 3)
                .map((issue, index) => (
                  <motion.div
                    key={issue.number}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-900 transition-colors group"
                  >
                    <div className={`p-1.5 rounded ${
                      issue.state === 'open' 
                        ? 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400'
                        : 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                    }`}>
                      {issue.state === 'open' ? (
                        <AlertCircle className="w-4 h-4" />
                      ) : (
                        <CheckCircle className="w-4 h-4" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h5 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-yellow-600 dark:group-hover:text-yellow-400 transition-colors">
                          {issue.title}
                        </h5>
                        <a
                          href={issue.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-shrink-0 text-gray-400 hover:text-yellow-600 dark:hover:text-yellow-400 transition-colors"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
                        <span>#{issue.number}</span>
                        <span>•</span>
                        <span>by {issue.author}</span>
                        <span>•</span>
                        <span>{new Date(issue.createdAt).toLocaleDateString()}</span>
                      </div>
                      {issue.labels && issue.labels.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {issue.labels.slice(0, 3).map((label) => (
                            <span
                              key={label}
                              className={`px-2 py-0.5 rounded text-xs ${getLabelColor(label)}`}
                            >
                              {label}
                            </span>
                          ))}
                          {issue.labels.length > 3 && (
                            <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                              +{issue.labels.length - 3}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
            </AnimatePresence>
          </div>

          {onViewAll && statistics.recent.length > 3 && (
            <button
              onClick={onViewAll}
              className="w-full mt-4 py-2 text-sm font-medium text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 rounded-lg transition-colors"
            >
              View All {statistics.total} Issues
            </button>
          )}
        </div>
      )}

      {/* Empty State */}
      {(!statistics.recent || statistics.recent.length === 0) && (
        <div className="p-6 text-center">
          <AlertCircle className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No issues found
          </p>
        </div>
      )}
    </motion.div>
  );
};

export default IssueStatisticsCard;
