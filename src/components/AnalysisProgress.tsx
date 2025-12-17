import React from 'react';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface AnalysisProgressData {
  total_repos: number;
  scored: number;
  categorized: number;
  evaluated: number;
  to_evaluate: number;
  percentage: number;
  current_message?: string;
}

interface AnalysisProgressProps {
  status: 'started' | 'scoring' | 'categorizing' | 'evaluating' | 'calculating' | 'complete' | 'failed';
  progress: AnalysisProgressData;
  message?: string;
  error?: string;
  className?: string;
}

const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  status,
  progress,
  message,
  error,
  className = ''
}) => {
  const getPhaseIcon = (phase: string, currentStatus: string) => {
    const phaseOrder = ['scoring', 'categorizing', 'evaluating', 'calculating', 'complete'];
    const currentIndex = phaseOrder.indexOf(currentStatus);
    const phaseIndex = phaseOrder.indexOf(phase);

    if (phaseIndex < currentIndex || currentStatus === 'complete') {
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    } else if (phaseIndex === currentIndex) {
      return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
    } else {
      return <div className="h-4 w-4 rounded-full border-2 border-gray-300" />;
    }
  };

  const getPhaseLabel = (phase: string) => {
    const labels: Record<string, string> = {
      scoring: 'Scoring',
      categorizing: 'Categorizing',
      evaluating: 'Evaluating',
      calculating: 'Calculating',
      complete: 'Complete'
    };
    return labels[phase] || phase;
  };

  const getStatusMessage = () => {
    if (error) return error;
    if (message) return message;
    if (progress.current_message) return progress.current_message;

    switch (status) {
      case 'started':
        return 'Starting analysis...';
      case 'scoring':
        return 'Calculating importance scores...';
      case 'categorizing':
        return 'Categorizing repositories...';
      case 'evaluating':
        return `Evaluating ${progress.evaluated} of ${progress.to_evaluate} repositories...`;
      case 'calculating':
        return 'Calculating overall score...';
      case 'complete':
        return `Analysis complete! ${progress.evaluated} repositories evaluated`;
      case 'failed':
        return 'Analysis failed';
      default:
        return 'Processing...';
    }
  };

  if (status === 'failed') {
    const isRateLimitError = error?.toLowerCase().includes('rate limit');
    
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`card p-6 ${
          isRateLimitError
            ? 'bg-yellow-50 border-2 border-yellow-200'
            : 'bg-red-50 border-2 border-red-200'
        } ${className}`}
      >
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <AlertCircle className={`h-6 w-6 flex-shrink-0 ${
              isRateLimitError ? 'text-yellow-600' : 'text-red-600'
            }`} />
            <div className="flex-1">
              <h3 className={`text-lg font-semibold ${
                isRateLimitError ? 'text-yellow-900' : 'text-red-900'
              }`}>
                {isRateLimitError ? 'Rate Limit Exceeded' : 'Analysis Failed'}
              </h3>
              <p className={`text-sm mt-1 ${
                isRateLimitError ? 'text-yellow-700' : 'text-red-700'
              }`}>
                {getStatusMessage()}
              </p>
            </div>
          </div>
          
          {/* Additional context for rate limits */}
          {isRateLimitError && (
            <div className="p-3 bg-yellow-100 rounded-lg border border-yellow-300">
              <p className="text-sm text-yellow-800">
                GitHub API rate limits have been reached. This typically resets within an hour. 
                Try again later or analyze a different profile.
              </p>
            </div>
          )}
          
          {/* Show partial progress if any */}
          {progress && progress.evaluated > 0 && (
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-800">
                <strong>Partial Progress:</strong> {progress.evaluated} of {progress.to_evaluate} repositories 
                were evaluated before the failure occurred.
              </p>
            </div>
          )}
        </div>
      </motion.div>
    );
  }

  if (status === 'complete') {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`card p-6 bg-green-50 border-2 border-green-200 ${className}`}
      >
        <div className="flex items-center space-x-3">
          <CheckCircle className="h-6 w-6 text-green-600 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-green-900">Analysis Complete</h3>
            <p className="text-sm text-green-700 mt-1">{getStatusMessage()}</p>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`card p-6 bg-blue-50 border-2 border-blue-200 ${className}`}
    >
      <div className="space-y-4">
        {/* Header with percentage */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Loader2 className="h-6 w-6 text-blue-600 animate-spin flex-shrink-0" />
            <h3 className="text-lg font-semibold text-gray-900">
              Analyzing Repositories
            </h3>
          </div>
          <div className="text-2xl font-bold text-blue-600">
            {progress.percentage}%
          </div>
        </div>

        {/* Progress Bar */}
        <div className="relative">
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress.percentage}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full"
            />
          </div>
        </div>

        {/* Status Message */}
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-gray-700">
            {getStatusMessage()}
          </p>
          {status === 'evaluating' && (
            <p className="text-sm text-gray-500">
              {progress.evaluated} / {progress.to_evaluate}
            </p>
          )}
        </div>

        {/* Phase Indicators */}
        <div className="flex items-center justify-between pt-2">
          {['scoring', 'categorizing', 'evaluating', 'calculating'].map((phase, index) => (
            <div key={phase} className="flex items-center">
              <div className="flex flex-col items-center space-y-1">
                {getPhaseIcon(phase, status)}
                <span className={`text-xs font-medium ${
                  phase === status
                    ? 'text-blue-600'
                    : ['scoring', 'categorizing', 'evaluating', 'calculating', 'complete'].indexOf(status) >
                      ['scoring', 'categorizing', 'evaluating', 'calculating'].indexOf(phase)
                    ? 'text-green-600'
                    : 'text-gray-400'
                }`}>
                  {getPhaseLabel(phase)}
                </span>
              </div>
              {index < 3 && (
                <div className={`h-0.5 w-8 mx-2 ${
                  ['scoring', 'categorizing', 'evaluating', 'calculating', 'complete'].indexOf(status) >
                  ['scoring', 'categorizing', 'evaluating', 'calculating'].indexOf(phase)
                    ? 'bg-green-600'
                    : 'bg-gray-300'
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Detailed Stats */}
        {status === 'evaluating' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="pt-3 border-t border-blue-200"
          >
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {progress.total_repos}
                </div>
                <div className="text-xs text-gray-500">Total Repos</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {progress.to_evaluate}
                </div>
                <div className="text-xs text-gray-500">To Evaluate</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {progress.evaluated}
                </div>
                <div className="text-xs text-gray-500">Evaluated</div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default AnalysisProgress;
