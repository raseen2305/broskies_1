import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Clock, TrendingUp, Zap, Database } from 'lucide-react';

interface EstimatedTimeDisplayProps {
  startTime: Date;
  currentProgress: number;
  totalRepositories: number;
  repositoriesProcessed: number;
  currentPhase: string;
  className?: string;
}

interface TimeEstimate {
  remaining: number;
  total: number;
  confidence: 'high' | 'medium' | 'low';
}

export const EstimatedTimeDisplay: React.FC<EstimatedTimeDisplayProps> = ({
  startTime,
  currentProgress,
  totalRepositories,
  repositoriesProcessed,
  currentPhase,
  className = ''
}) => {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [estimate, setEstimate] = useState<TimeEstimate>({ remaining: 0, total: 0, confidence: 'low' });

  // Phase-based time estimates (in seconds per repository)
  const phaseTimeEstimates = {
    connecting: 2,
    profile: 3,
    repositories: 8,
    analysis: 15,
    insights: 5,
    completed: 0
  };

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const elapsed = (now.getTime() - startTime.getTime()) / 1000;
      setElapsedTime(elapsed);

      // Calculate estimated remaining time
      if (currentProgress > 5) {
        const timePerPercent = elapsed / currentProgress;
        const remainingProgress = 100 - currentProgress;
        const estimatedRemaining = timePerPercent * remainingProgress;
        
        // Adjust based on current phase
        const phaseMultiplier = phaseTimeEstimates[currentPhase as keyof typeof phaseTimeEstimates] || 10;
        const repositoryAdjustment = Math.max(1, totalRepositories / 10);
        
        const adjustedRemaining = estimatedRemaining * repositoryAdjustment;
        const totalEstimated = elapsed + adjustedRemaining;
        
        // Determine confidence based on progress
        let confidence: 'high' | 'medium' | 'low' = 'low';
        if (currentProgress > 50) confidence = 'high';
        else if (currentProgress > 20) confidence = 'medium';

        setEstimate({
          remaining: Math.max(0, adjustedRemaining),
          total: totalEstimated,
          confidence
        });
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime, currentProgress, currentPhase, totalRepositories]);

  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'text-green-600 bg-green-50 border-green-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case 'analysis': return Zap;
      case 'repositories': return Database;
      case 'insights': return TrendingUp;
      default: return Clock;
    }
  };

  const PhaseIcon = getPhaseIcon(currentPhase);

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Time Estimate</h3>
        <PhaseIcon className="h-5 w-5 text-gray-400" />
      </div>

      <div className="space-y-4">
        {/* Elapsed Time */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Elapsed</span>
          <motion.span 
            key={Math.floor(elapsedTime)}
            initial={{ scale: 1.1 }}
            animate={{ scale: 1 }}
            className="text-lg font-mono font-semibold text-gray-900"
          >
            {formatTime(elapsedTime)}
          </motion.span>
        </div>

        {/* Estimated Remaining */}
        {estimate.remaining > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Remaining</span>
            <motion.span 
              key={Math.floor(estimate.remaining / 10)}
              initial={{ opacity: 0.7 }}
              animate={{ opacity: 1 }}
              className="text-lg font-mono font-semibold text-primary-600"
            >
              ~{formatTime(estimate.remaining)}
            </motion.span>
          </div>
        )}

        {/* Total Estimated */}
        {estimate.total > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Total Est.</span>
            <span className="text-sm font-mono text-gray-700">
              {formatTime(estimate.total)}
            </span>
          </div>
        )}

        {/* Confidence Indicator */}
        {currentProgress > 5 && (
          <div className={`p-3 rounded-lg border ${getConfidenceColor(estimate.confidence)}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Estimate Confidence</span>
              <span className="text-sm capitalize font-semibold">
                {estimate.confidence}
              </span>
            </div>
            <div className="mt-2 text-xs opacity-75">
              {estimate.confidence === 'high' && 'Based on current progress pattern'}
              {estimate.confidence === 'medium' && 'Estimate improving as scan progresses'}
              {estimate.confidence === 'low' && 'Early estimate, accuracy will improve'}
            </div>
          </div>
        )}

        {/* Progress Rate */}
        {currentProgress > 10 && elapsedTime > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Progress Rate</span>
              <span className="font-medium text-gray-900">
                {(currentProgress / elapsedTime * 60).toFixed(1)}%/min
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};