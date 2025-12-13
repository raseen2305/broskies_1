import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertCircle, 
  RefreshCw, 
  ArrowLeft, 
  Shield, 
  Clock, 
  Wifi, 
  Github,
  Key,
  Lock,
  AlertTriangle,
  Info
} from 'lucide-react';

interface ScanError {
  id: string;
  type: 'rate_limit' | 'private_repo' | 'network' | 'auth' | 'api' | 'timeout' | 'unknown';
  message: string;
  details?: string;
  repository?: string;
  timestamp: Date;
  recoverable: boolean;
  retryAfter?: number; // seconds
}

interface ErrorDisplayHandlerProps {
  errors: ScanError[];
  onRetry?: () => void;
  onCancel?: () => void;
  onRetryRepository?: (repository: string) => void;
  isRetrying?: boolean;
  className?: string;
}

const errorTypeConfig = {
  rate_limit: {
    icon: Clock,
    title: 'Rate Limit Reached',
    color: 'yellow',
    description: 'GitHub API rate limit exceeded. Please wait before retrying.',
    actionable: true
  },
  private_repo: {
    icon: Lock,
    title: 'Private Repository',
    color: 'blue',
    description: 'This repository is private and cannot be accessed.',
    actionable: false
  },
  network: {
    icon: Wifi,
    title: 'Network Error',
    color: 'red',
    description: 'Unable to connect to GitHub. Check your internet connection.',
    actionable: true
  },
  auth: {
    icon: Key,
    title: 'Authentication Error',
    color: 'red',
    description: 'GitHub authentication failed. Please check your token.',
    actionable: true
  },
  api: {
    icon: Github,
    title: 'GitHub API Error',
    color: 'red',
    description: 'GitHub API returned an error. This may be temporary.',
    actionable: true
  },
  timeout: {
    icon: Clock,
    title: 'Request Timeout',
    color: 'orange',
    description: 'Request took too long to complete. This may be due to large repositories.',
    actionable: true
  },
  unknown: {
    icon: AlertCircle,
    title: 'Unknown Error',
    color: 'red',
    description: 'An unexpected error occurred during scanning.',
    actionable: true
  }
};

const getColorClasses = (color: string) => {
  const colorMap = {
    red: 'bg-red-50 border-red-200 text-red-800',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    orange: 'bg-orange-50 border-orange-200 text-orange-800'
  };
  return colorMap[color as keyof typeof colorMap] || colorMap.red;
};

const getIconColorClasses = (color: string) => {
  const colorMap = {
    red: 'text-red-500',
    yellow: 'text-yellow-500',
    blue: 'text-blue-500',
    orange: 'text-orange-500'
  };
  return colorMap[color as keyof typeof colorMap] || colorMap.red;
};

export const ErrorDisplayHandler: React.FC<ErrorDisplayHandlerProps> = ({
  errors,
  onRetry,
  onCancel,
  onRetryRepository,
  isRetrying = false,
  className = ''
}) => {
  if (errors.length === 0) return null;

  // Group errors by type
  const errorsByType = errors.reduce((acc, error) => {
    if (!acc[error.type]) acc[error.type] = [];
    acc[error.type].push(error);
    return acc;
  }, {} as Record<string, ScanError[]>);

  // Get the most recent critical error
  const criticalErrors = errors.filter(e => ['auth', 'network'].includes(e.type));
  const mostRecentCritical = criticalErrors[criticalErrors.length - 1];

  // Count recoverable vs non-recoverable errors
  const recoverableCount = errors.filter(e => e.recoverable).length;
  const totalErrors = errors.length;

  const formatTimeUntilRetry = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Critical Error Display */}
      {mostRecentCritical && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl border-l-4 border-red-500 shadow-lg p-6"
        >
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <AlertCircle className="h-8 w-8 text-red-500" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-900 mb-2">
                Scan Failed: {errorTypeConfig[mostRecentCritical.type].title}
              </h3>
              <p className="text-red-700 mb-4">
                {mostRecentCritical.message}
              </p>
              <div className="flex space-x-3">
                {mostRecentCritical.recoverable && onRetry && (
                  <button
                    onClick={onRetry}
                    disabled={isRetrying}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isRetrying ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4 mr-2" />
                    )}
                    Retry Scan
                  </button>
                )}
                {onCancel && (
                  <button
                    onClick={onCancel}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Go Back
                  </button>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Error Summary */}
      {!mostRecentCritical && totalErrors > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl border border-orange-200 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <AlertTriangle className="h-6 w-6 text-orange-500" />
              <h3 className="text-lg font-semibold text-orange-900">
                Scan Completed with Issues
              </h3>
            </div>
            <div className="text-sm text-orange-700">
              {totalErrors} error{totalErrors !== 1 ? 's' : ''} encountered
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="bg-orange-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-orange-900">{recoverableCount}</div>
              <div className="text-sm text-orange-700">Recoverable Issues</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-gray-900">{totalErrors - recoverableCount}</div>
              <div className="text-sm text-gray-700">Permanent Issues</div>
            </div>
          </div>

          {recoverableCount > 0 && onRetry && (
            <button
              onClick={onRetry}
              disabled={isRetrying}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-orange-600 rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isRetrying ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Retry Failed Items
            </button>
          )}
        </motion.div>
      )}

      {/* Detailed Error List */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-900">Error Details</h4>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          <AnimatePresence>
            {Object.entries(errorsByType).map(([type, typeErrors]) => {
              const config = errorTypeConfig[type as keyof typeof errorTypeConfig];
              const IconComponent = config.icon;
              const colorClasses = getColorClasses(config.color);
              const iconColorClasses = getIconColorClasses(config.color);
              
              return typeErrors.map((error, index) => (
                <motion.div
                  key={error.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className={`flex items-start space-x-3 p-4 rounded-lg border ${colorClasses}`}
                >
                  <IconComponent className={`h-5 w-5 mt-0.5 flex-shrink-0 ${iconColorClasses}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h5 className="text-sm font-semibold">{config.title}</h5>
                      {error.retryAfter && (
                        <span className="text-xs opacity-75">
                          Retry in {formatTimeUntilRetry(error.retryAfter)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm mb-2">{error.message}</p>
                    {error.details && (
                      <p className="text-xs opacity-75 mb-2">{error.details}</p>
                    )}
                    {error.repository && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs opacity-75">
                          Repository: {error.repository}
                        </span>
                        {error.recoverable && onRetryRepository && (
                          <button
                            onClick={() => onRetryRepository(error.repository!)}
                            className="text-xs font-medium hover:underline"
                          >
                            Retry
                          </button>
                        )}
                      </div>
                    )}
                    <p className="text-xs opacity-60 mt-1">
                      {error.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </motion.div>
              ));
            })}
          </AnimatePresence>
        </div>
      </div>

      {/* Help and Tips */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="bg-blue-50 border border-blue-200 rounded-lg p-4"
      >
        <div className="flex items-start space-x-3">
          <Info className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-2">Troubleshooting Tips:</p>
            <ul className="space-y-1 text-xs">
              <li>• Rate limits reset every hour - wait and retry later</li>
              <li>• Private repositories require appropriate access permissions</li>
              <li>• Network errors are usually temporary - try again in a few minutes</li>
              <li>• Large repositories may timeout - this is normal and can be retried</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  );
};