import React from 'react';
import { motion } from 'framer-motion';
import { GitBranch, Star, GitFork, Code, CheckCircle, AlertCircle } from 'lucide-react';

interface RepositoryStats {
  name: string;
  language: string;
  stars: number;
  forks: number;
  status: 'pending' | 'analyzing' | 'completed' | 'error';
  score?: number;
}

interface RepositoryCounterProps {
  currentRepository: string;
  repositoriesProcessed: number;
  totalRepositories: number;
  recentRepositories?: RepositoryStats[];
  averageScore?: number;
  className?: string;
}

export const RepositoryCounter: React.FC<RepositoryCounterProps> = ({
  currentRepository,
  repositoriesProcessed,
  totalRepositories,
  recentRepositories = [],
  averageScore,
  className = ''
}) => {
  const progressPercentage = totalRepositories > 0 ? (repositoriesProcessed / totalRepositories) * 100 : 0;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return CheckCircle;
      case 'error': return AlertCircle;
      case 'analyzing': return Code;
      default: return GitBranch;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-500';
      case 'error': return 'text-red-500';
      case 'analyzing': return 'text-blue-500';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Repository Analysis</h3>
        <div className="flex items-center space-x-2">
          <GitBranch className="h-5 w-5 text-gray-400" />
          <span className="text-sm text-gray-600">
            {repositoriesProcessed} / {totalRepositories}
          </span>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="space-y-4 mb-6">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          <span className="text-lg font-bold text-primary-600">
            {Math.round(progressPercentage)}%
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3">
          <motion.div
            className="h-3 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progressPercentage}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>

        {/* Current Repository */}
        {currentRepository && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-blue-50 border border-blue-200 rounded-lg p-3"
          >
            <div className="flex items-center space-x-2">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Code className="h-4 w-4 text-blue-500" />
              </motion.div>
              <span className="text-sm font-medium text-blue-900">
                Analyzing: {currentRepository}
              </span>
            </div>
          </motion.div>
        )}
      </div>

      {/* Statistics */}
      {averageScore !== undefined && repositoriesProcessed > 0 && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{Math.round(averageScore)}</div>
            <div className="text-xs text-gray-600">Avg Score</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{repositoriesProcessed}</div>
            <div className="text-xs text-gray-600">Analyzed</div>
          </div>
        </div>
      )}

      {/* Recent Repositories */}
      {recentRepositories.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">Recent Analysis</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {recentRepositories.slice(-5).reverse().map((repo, index) => {
              const StatusIcon = getStatusIcon(repo.status);
              const statusColor = getStatusColor(repo.status);
              
              return (
                <motion.div
                  key={`${repo.name}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <StatusIcon className={`h-4 w-4 ${statusColor} flex-shrink-0`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {repo.name}
                      </p>
                      <div className="flex items-center space-x-3 text-xs text-gray-500">
                        <span>{repo.language}</span>
                        <div className="flex items-center space-x-1">
                          <Star className="h-3 w-3" />
                          <span>{repo.stars}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <GitFork className="h-3 w-3" />
                          <span>{repo.forks}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  {repo.score !== undefined && repo.status === 'completed' && (
                    <div className="text-sm font-semibold text-primary-600">
                      {Math.round(repo.score)}
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};