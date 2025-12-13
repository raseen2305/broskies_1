import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, Clock, CheckCircle, AlertCircle, Pause, Play } from 'lucide-react';

interface RetryAttempt {
  id: string;
  timestamp: Date;
  reason: string;
  success: boolean;
  error?: string;
}

interface RetryMechanismProps {
  onRetry: () => Promise<void>;
  maxAttempts?: number;
  retryDelay?: number; // seconds
  exponentialBackoff?: boolean;
  autoRetry?: boolean;
  retryableErrors?: string[];
  className?: string;
}

export const RetryMechanism: React.FC<RetryMechanismProps> = ({
  onRetry,
  maxAttempts = 3,
  retryDelay = 5,
  exponentialBackoff = true,
  autoRetry = false,
  retryableErrors = ['network', 'timeout', 'rate_limit'],
  className = ''
}) => {
  const [attempts, setAttempts] = useState<RetryAttempt[]>([]);
  const [isRetrying, setIsRetrying] = useState(false);
  const [nextRetryIn, setNextRetryIn] = useState<number | null>(null);
  const [autoRetryEnabled, setAutoRetryEnabled] = useState(autoRetry);
  const [retryTimer, setRetryTimer] = useState<number | null>(null);

  const currentAttempt = attempts.length;
  const canRetry = currentAttempt < maxAttempts;
  const hasFailedAttempts = attempts.some(a => !a.success);

  // Calculate next retry delay with exponential backoff
  const getRetryDelay = (attemptNumber: number) => {
    if (!exponentialBackoff) return retryDelay;
    return retryDelay * Math.pow(2, attemptNumber - 1);
  };

  // Handle manual retry
  const handleManualRetry = async (reason: string = 'Manual retry') => {
    if (!canRetry || isRetrying) return;

    setIsRetrying(true);
    const attemptId = `attempt-${Date.now()}`;
    
    try {
      await onRetry();
      
      // Record successful attempt
      setAttempts(prev => [...prev, {
        id: attemptId,
        timestamp: new Date(),
        reason,
        success: true
      }]);
      
      // Clear any pending auto-retry
      if (retryTimer) {
        clearTimeout(retryTimer);
        setRetryTimer(null);
      }
      setNextRetryIn(null);
      
    } catch (error) {
      // Record failed attempt
      setAttempts(prev => [...prev, {
        id: attemptId,
        timestamp: new Date(),
        reason,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }]);
      
      // Schedule auto-retry if enabled and we can still retry
      if (autoRetryEnabled && currentAttempt + 1 < maxAttempts) {
        scheduleAutoRetry(currentAttempt + 1);
      }
    } finally {
      setIsRetrying(false);
    }
  };

  // Schedule automatic retry
  const scheduleAutoRetry = (attemptNumber: number) => {
    const delay = getRetryDelay(attemptNumber);
    setNextRetryIn(delay);
    
    // Start countdown
    const countdownInterval = setInterval(() => {
      setNextRetryIn(prev => {
        if (prev === null || prev <= 1) {
          clearInterval(countdownInterval);
          return null;
        }
        return prev - 1;
      });
    }, 1000);
    
    // Schedule the actual retry
    const timeout = setTimeout(() => {
      clearInterval(countdownInterval);
      setNextRetryIn(null);
      handleManualRetry('Automatic retry');
    }, delay * 1000);
    
    setRetryTimer(timeout);
  };

  // Cancel auto-retry
  const cancelAutoRetry = () => {
    if (retryTimer) {
      clearTimeout(retryTimer);
      setRetryTimer(null);
    }
    setNextRetryIn(null);
  };

  // Toggle auto-retry
  const toggleAutoRetry = () => {
    setAutoRetryEnabled(prev => {
      const newValue = !prev;
      if (!newValue) {
        cancelAutoRetry();
      }
      return newValue;
    });
  };

  // Reset retry state
  const resetRetries = () => {
    setAttempts([]);
    cancelAutoRetry();
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (retryTimer) {
        clearTimeout(retryTimer);
      }
    };
  }, [retryTimer]);

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Retry Control</h3>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">
            {currentAttempt}/{maxAttempts} attempts
          </span>
        </div>
      </div>

      {/* Retry Status */}
      <div className="space-y-4">
        {/* Current Status */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            {isRetrying ? (
              <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />
            ) : nextRetryIn ? (
              <Clock className="h-5 w-5 text-yellow-500" />
            ) : hasFailedAttempts ? (
              <AlertCircle className="h-5 w-5 text-red-500" />
            ) : (
              <CheckCircle className="h-5 w-5 text-green-500" />
            )}
            
            <div>
              <p className="text-sm font-medium text-gray-900">
                {isRetrying ? 'Retrying...' :
                 nextRetryIn ? `Auto-retry in ${formatTime(nextRetryIn)}` :
                 hasFailedAttempts ? 'Ready to retry' :
                 'No retries needed'}
              </p>
              {nextRetryIn && (
                <p className="text-xs text-gray-600">
                  Attempt {currentAttempt + 1} of {maxAttempts}
                </p>
              )}
            </div>
          </div>
          
          {/* Auto-retry toggle */}
          <button
            onClick={toggleAutoRetry}
            className={`flex items-center space-x-2 px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              autoRetryEnabled 
                ? 'bg-blue-100 text-blue-800 hover:bg-blue-200' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {autoRetryEnabled ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
            <span>Auto-retry</span>
          </button>
        </div>

        {/* Manual Retry Button */}
        <div className="flex space-x-3">
          <button
            onClick={() => handleManualRetry()}
            disabled={!canRetry || isRetrying}
            className="flex-1 inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isRetrying ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Retry Now
          </button>
          
          {nextRetryIn && (
            <button
              onClick={cancelAutoRetry}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
          )}
          
          {attempts.length > 0 && (
            <button
              onClick={resetRetries}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Reset
            </button>
          )}
        </div>

        {/* Retry History */}
        {attempts.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Retry History</h4>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {attempts.map((attempt, index) => (
                <motion.div
                  key={attempt.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`flex items-center justify-between p-2 rounded text-sm ${
                    attempt.success 
                      ? 'bg-green-50 text-green-800' 
                      : 'bg-red-50 text-red-800'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    {attempt.success ? (
                      <CheckCircle className="h-3 w-3" />
                    ) : (
                      <AlertCircle className="h-3 w-3" />
                    )}
                    <span>Attempt {index + 1}: {attempt.reason}</span>
                  </div>
                  <span className="text-xs opacity-75">
                    {attempt.timestamp.toLocaleTimeString()}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Retry Configuration Info */}
        <div className="text-xs text-gray-500 space-y-1">
          <p>• Maximum {maxAttempts} retry attempts allowed</p>
          <p>• Base retry delay: {retryDelay} seconds</p>
          {exponentialBackoff && <p>• Exponential backoff enabled</p>}
        </div>
      </div>
    </div>
  );
};